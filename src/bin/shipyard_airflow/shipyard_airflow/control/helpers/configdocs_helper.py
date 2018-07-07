# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Configdocs helper primarily masquerades as a layer in front of
Deckhand, providing a representation of a buffer and a committed
bucket for Shipyard
"""
import enum
import logging
import threading

import falcon
from oslo_config import cfg
import requests

from shipyard_airflow.common.document_validators.document_validator_manager \
    import DocumentValidationManager
from shipyard_airflow.control import service_clients
from shipyard_airflow.control.helpers.design_reference_helper import \
    DesignRefHelper
from shipyard_airflow.control.helpers.deckhand_client import (
    DeckhandClient, DeckhandError, DeckhandRejectedInputError,
    DeckhandResponseError, DocumentExistsElsewhereError, NoRevisionsExistError)
from shipyard_airflow.control.service_endpoints import (
    Endpoints, get_endpoint, get_token)
from shipyard_airflow.control.validators.validate_deployment_configuration \
    import ValidateDeploymentConfigurationFull
from shipyard_airflow.errors import ApiError, AppError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

# keys for the revision dict, and consistency of strings for committed,
# buffer, site-action-success and site-action-failure.
BUFFER = 'buffer'
COMMITTED = 'committed'
LAST_SITE_ACTION = 'last_site_action'
LATEST = 'latest'
REVISION_COUNT = 'count'
SITE_ACTION_SUCCESS = 'site-action-success'
SITE_ACTION_FAILURE = 'site-action-failure'
SUCCESSFUL_SITE_ACTION = 'successful_site_action'

# string for rollback_commit consistency
ROLLBACK_COMMIT = 'rollback_commit'


class BufferMode(enum.Enum):
    """
    Enumeration of the valid values for BufferMode
    """
    REJECTONCONTENTS = 'rejectoncontents'
    APPEND = 'append'
    REPLACE = 'replace'


class ConfigdocsHelper(object):
    """
    ConfigdocsHelper provides a layer to represent the buffer and committed
    versions of design documents.
    A new configdocs_helper is intended to be used for each invocation of the
    service.
    """

    def __init__(self, context):
        """
        Sets up this Configdocs helper with the supplied
        request context
        """
        self.deckhand = DeckhandClient(context.external_marker)
        self.ctx = context
        # The revision_dict indicates the revisions that are
        # associated with the buffered and committed doc sets. There
        # is a risk of this being out of sync if there is high volume
        # of commits and adds of docs going on in parallel, but not
        # really much more than if this data is used in subsequent
        # statements following a call within a method.
        self.revision_dict = None

    @staticmethod
    def get_buffer_mode(buffermode_string=None):
        """Checks the buffer mode for valid values.

        :param buffermode_string: the string matching a valid buffer mode
        Returns Buffermode.REJECTONTENTS value if the input is not specified
        or is an invalid value.
        """
        if buffermode_string:
            try:
                buffer_mode = BufferMode(buffermode_string.lower())
                return buffer_mode
            except ValueError:
                return None
        return BufferMode.REJECTONCONTENTS

    def is_buffer_empty(self):
        """ Check if the buffer is empty. """
        return self._get_revision(BUFFER) is None

    def is_collection_in_buffer(self, collection_id):
        """
        Returns if the collection is represented in the buffer
        """
        if self.is_buffer_empty():
            return False

        # If there is no committed revision, then it's 0.
        # new revision is ok because we just checked for buffer emptiness
        old_revision_id = self.get_revision_id(COMMITTED) or 0

        try:
            diff = self.deckhand.get_diff(
                old_revision_id=old_revision_id,
                new_revision_id=self.get_revision_id(BUFFER))
            # the collection is in the buffer if it's not unmodified
            return diff.get(collection_id, 'unmodified') != 'unmodified'

        except DeckhandResponseError as drex:
            raise AppError(
                title='Unable to retrieve revisions',
                description=(
                    'Deckhand has responded unexpectedly: {}:{}'.format(
                        drex.status_code, drex.response_message)),
                status=falcon.HTTP_500,
                retry=False, )

    def is_buffer_valid_for_bucket(self, collection_id, buffermode):
        """
        Indicates if the buffer as it currently is, may be written to
        for the specified collection, based on the buffermode.
        """
        # can always write if buffer is empty.
        if self.is_buffer_empty():
            return True
        # from here down, the buffer is NOT empty.
        # determine steps by the buffermode
        if buffermode == BufferMode.REJECTONCONTENTS:
            return False
        elif buffermode == BufferMode.APPEND:
            return not self.is_collection_in_buffer(collection_id)
        # replace the buffer with last commit.
        elif buffermode == BufferMode.REPLACE:
            committed_rev_id = None
            committed_rev = self._get_revision(COMMITTED)
            if committed_rev:
                committed_rev_id = committed_rev['id']
            if committed_rev_id is None:
                # TODO (bryan-strassner) use rollback to 0 if/when that
                #     is implemented in deckhand.
                #     reset_to_empty has side effect of deleting history
                #     from deckhand although it is only the corner case
                #     where no commit has ever been done.
                self.deckhand.reset_to_empty()
            else:
                self.deckhand.rollback(committed_rev_id)
            return True

    def get_configdocs_status(self, versions=None):
        """
        :param versions: A list of 2 versions. Defaults to buffer and
                         commmitted if None.

        Returns a list of the configdocs based on their versions and
        statuses
        """
        configdocs_status = []

        # Get ordered versions
        ordered_versions = self._get_ordered_versions(versions)

        # Get version name and id
        old_version_name, new_version_name, old_version_id, new_version_id = (
            self._get_versions_name_id(ordered_versions))

        try:
            diff = self.deckhand.get_diff(
                old_revision_id=old_version_id,
                new_revision_id=new_version_id)

        except DeckhandResponseError as drex:
            raise AppError(
                title='Unable to retrieve revisions',
                description=(
                    'Deckhand has responded unexpectedly: {}:{}'.format(
                        drex.status_code, drex.response_message)),
                status=falcon.HTTP_500,
                retry=False, )

        for collection_id in diff:
            collection = {"collection_name": collection_id}

            if diff[collection_id] in [
                    "unmodified", "modified", "created", "deleted"]:

                collection['base_version'] = old_version_name
                collection['base_revision'] = old_version_id
                collection['new_version'] = new_version_name
                collection['new_revision'] = new_version_id
                collection['new_status'] = diff[collection_id]

                if diff[collection_id] == "created":
                    collection['base_status'] = 'not present'
                else:
                    collection['base_status'] = 'present'

            else:
                raise AppError(
                    title='Invalid collection status',
                    description=(
                        'Collection_id, {} has an invalid collection status. '
                        'unmodified, modified, created, and deleted are the'
                        ' only valid collection statuses.',
                        collection_id),
                    status=falcon.HTTP_500,
                    retry=False)

            configdocs_status.append(collection)

        return configdocs_status

    def _get_revision_dict(self):
        """
        Returns a dictionary with values representing the revisions in
        Deckhand that Shipyard cares about - committed, buffer, latest,
        last_site_action and successful_site_action, as well as a count
        of revisions.
        Committed and buffer are revisions associated with the
        shipyard tags. If either of those are not present in deckhand,
        returns None for the value.
        Latest holds the revision information for the newest revision.
        Last site action holds the revision information for the most
        recent site action
        Successful site action holds the revision information for the
        most recent successfully executed site action.
        """
        # return the cached instance version of the revision dict.
        if self.revision_dict is not None:
            return self.revision_dict
        # or generate one for the cache
        committed_revision = None
        buffer_revision = None
        last_site_action = None
        latest_revision = None
        revision_count = 0
        successful_site_action = None
        try:
            revisions = self.deckhand.get_revision_list()
            revision_count = len(revisions)
            if revisions:
                # Retrieve latest revision
                latest_revision = revisions[-1]

                # Get required revision
                for revision in reversed(revisions):
                    tags = revision.get('tags', [])

                    if (committed_revision is None and (
                            COMMITTED in tags or
                            ROLLBACK_COMMIT in tags)):
                        committed_revision = revision
                    else:
                        # there are buffer revisions, only grab it on
                        # the first pass through
                        # if the first revision is committed, or if there
                        # are no revsisions, buffer revsision stays None
                        if (committed_revision is None and
                                buffer_revision is None):
                            buffer_revision = revision

                    # Get the revision of the last successful site action
                    if (successful_site_action is None and
                            SITE_ACTION_SUCCESS in tags):
                        successful_site_action = revision

                    # Get the revision of the last site action
                    if (last_site_action is None and (
                            SITE_ACTION_SUCCESS in tags or
                            SITE_ACTION_FAILURE in tags)):
                        last_site_action = revision

        except NoRevisionsExistError:
            # the values of None/None/None/0 are fine
            pass

        except DeckhandResponseError as drex:
            raise AppError(
                title='Unable to retrieve revisions',
                description=(
                    'Deckhand has responded unexpectedly: {}:{}'.format(
                        drex.status_code, drex.response_message)),
                status=falcon.HTTP_500,
                retry=False)
        self.revision_dict = {
            BUFFER: buffer_revision,
            COMMITTED: committed_revision,
            LAST_SITE_ACTION: last_site_action,
            LATEST: latest_revision,
            REVISION_COUNT: revision_count,
            SUCCESSFUL_SITE_ACTION: successful_site_action
        }
        return self.revision_dict

    def _get_revision(self, target_revision):
        # Helper to drill down to the target revision
        return self._get_revision_dict().get(target_revision)

    def get_revision_id(self, target_revision):
        """Get the revision id for the target_revision"""
        rev = self._get_revision_dict().get(target_revision)
        return rev['id'] if rev else None

    def get_collection_docs(self, version, collection_id):
        """
        Returns the requested collection of docs based on the version
        specifier. The default is set as buffer.
        """
        LOG.info('Retrieving collection %s from %s', collection_id, version)
        if version in [COMMITTED, LAST_SITE_ACTION, SUCCESSFUL_SITE_ACTION]:
            return self._get_target_docs(collection_id, version)

        return self._get_doc_from_buffer(collection_id)

    def _get_doc_from_buffer(self, collection_id):
        """
        Returns the collection if it exists in the buffer.
        If the buffer contains the collection, the latest
        representation is what we want.
        """
        # Need to guard with this check for buffer to ensure
        # that the collection is not just carried through unmodified
        # into the buffer, and is actually represented.
        if self.is_collection_in_buffer(collection_id):
            # prior check for collection in buffer means the buffer
            # revision exists
            buffer_id = self.get_revision_id(BUFFER)
            return self.deckhand.get_docs_from_revision(
                revision_id=buffer_id, bucket_id=collection_id)
        raise ApiError(
            title='No documents to retrieve',
            description=('The Shipyard buffer is empty or does not contain '
                         'this collection'),
            status=falcon.HTTP_404,
            retry=False)

    def _get_target_docs(self, collection_id, target_rev):
        """
        Returns the collection if it exists as committed, last_site_action
        or successful_site_action.
        """
        revision_id = self.get_revision_id(target_rev)

        if revision_id:
            return self.deckhand.get_docs_from_revision(
                revision_id=revision_id, bucket_id=collection_id)

        raise ApiError(
            title='No documents to retrieve',
            description=('No collection {} for revision '
                         '{}'.format(collection_id, target_rev)),
            status=falcon.HTTP_404,
            retry=False)

    def get_rendered_configdocs(self, version=BUFFER):
        """
        Returns the rendered configuration documents for the specified
        revision (by name BUFFER, COMMITTED, LAST_SITE_ACTION,
        SUCCESSFUL_SITE_ACTION)
        """
        revision_dict = self._get_revision_dict()

        # Raise Exceptions if we received unexpected version
        if version not in [BUFFER, COMMITTED, LAST_SITE_ACTION,
                           SUCCESSFUL_SITE_ACTION]:
            raise ApiError(
                title='Invalid version',
                description='{} is not a valid version'.format(version),
                status=falcon.HTTP_400,
                retry=False)

        if revision_dict.get(version):
            revision_id = revision_dict.get(version).get('id')

            try:
                return self.deckhand.get_rendered_docs_from_revision(
                    revision_id=revision_id)
            except DeckhandError as de:
                raise ApiError(
                    title='Deckhand indicated an error while rendering',
                    description=de.response_message,
                    status=falcon.HTTP_500,
                    retry=False)

        else:
            raise ApiError(
                title='This revision does not exist',
                description='{} version does not exist'.format(version),
                status=falcon.HTTP_404,
                retry=False)

    def _get_validations_from_ucp_components(self, revision_id):
        """Invoke other UCP components to retrieve their validations"""
        resp_msgs = []
        error_count = 0
        design_ref = DesignRefHelper().get_design_reference(revision_id)

        validation_threads = _get_validation_threads(
            _get_validation_endpoints(), self.ctx, design_ref)
        # trigger each validation in parallel
        for validation_thread in validation_threads:
            if validation_thread.get('thread'):
                validation_thread.get('thread').start()
        # wait for all validations to return
        for validation_thread in validation_threads:
            validation_thread.get('thread').join()

        # check on the response, extract the validations
        for validation_thread in validation_threads:
            th_name = validation_thread.get('name')
            val_response = validation_thread.get('response',
                                                 {}).get('response')
            LOG.debug("Validation from:  %s response: %s", th_name,
                      str(val_response))
            if validation_thread.get('exception', {}).get('exception'):
                LOG.error('Invocation of validation by %s has failed', th_name)
            # invalid status needs collection of messages
            # valid status means that it passed. No messages to collect
            if val_response.get('details') is None:
                msg_list = [{'message': str(val_response), 'error': True}]
            else:
                msg_list = val_response.get('details').get('messageList', [])
            for msg in msg_list:
                # Count errors, convert message to ValidationMessage
                default_level = 'Info'
                if msg.get('error'):
                    error_count = error_count + 1
                    default_level = 'Error'
                val_msg = _generate_validation_message(
                    msg, level=default_level, source=th_name
                )
                resp_msgs.append(val_msg)
        return (error_count, resp_msgs)

    def get_validations_for_revision(self, revision_id):
        """Retrieves validations for a revision

        Invokes Deckhand to render the revision, which will either succeed, or
        fail and return validaiton failures. If there are any failures, the
        process will not proceed to validate against the other UCP components.
        Upon success from Deckhand rendering, uses the endpoints for each of
        the UCP components to validate the version indicated.
        Responds in the format defined here:
        https://github.com/att-comdev/ucp-integration/blob/master/docs/api-conventions.md#post-v10validatedesign
        """
        resp_msgs = []
        error_count = 0

        # Capture the messages from trying to render the revision.
        render_errors = self.deckhand.get_render_errors(revision_id)
        resp_msgs.extend(render_errors)
        error_count += len(render_errors)
        LOG.debug("Deckhand errors from rendering: %s", error_count)
        # Incorporate stored validation errors from Deckhand (prevalidations)
        # Note: This may have to change to be later in the code if we store
        # validations from other sources in Deckhand.
        dh_validations = self._get_deckhand_validation_errors(revision_id)
        error_count += len(dh_validations)
        resp_msgs.extend(dh_validations)
        LOG.debug("Deckhand validations: %s", len(dh_validations))

        # Only invoke the other validations if Deckhand has not returned any.
        if (error_count == 0):
            # Start with Shipyard's own validations
            results = self._get_shipyard_validations(revision_id)
            err_results = [r for r in results if r['error']]
            error_count += len(err_results)
            resp_msgs.extend(results)

            # And then the other ucp components
            (cpnt_ec, cpnt_msgs) = self._get_validations_from_ucp_components(
                revision_id)
            resp_msgs.extend(cpnt_msgs)
            error_count += cpnt_ec
            LOG.debug("UCP component validations: %s", cpnt_ec)

        # return the formatted status response
        return _format_validations_to_status(resp_msgs, error_count)

    def _get_shipyard_validations(self, revision_id):
        # Run Shipyard's own validations.
        try:
            sy_val_mgr = DocumentValidationManager(
                service_clients.deckhand_client(),
                revision_id,
                [(ValidateDeploymentConfigurationFull,
                  'deployment-configuration')]
            )
            return sy_val_mgr.validate()
        except Exception as ex:
            # Don't let any exceptions here prevent subsequent processing,
            # but make sure we register an error to prevent success.
            return [_generate_validation_message({
                "error": True,
                "message": ("Shipyard has encountered an unexpected error "
                            "while processing document validations"),
                "name": "DocumentValidationProcessingError",
                "diagnostic": str(ex),
            })]

    def get_deckhand_validation_status(self, revision_id):
        """Retrieve Deckhand validation status

        Returns the status object representing the deckhand validation results
        """
        dh_validations = self._get_deckhand_validation_errors(revision_id)
        error_count = len(dh_validations)
        return _format_validations_to_status(dh_validations, error_count)

    def _get_deckhand_validation_errors(self, revision_id):
        # Returns stored validation errors that deckhand has for this revision.
        resp_msgs = []
        deckhand_val = self.deckhand.get_all_revision_validations(revision_id)
        if deckhand_val.get('results'):
            for dh_result in deckhand_val.get('results'):
                if dh_result.get('errors'):
                    for error in dh_result.get('errors'):
                        resp_msgs.append(
                            _generate_dh_val_msg(
                                error, dh_result_name=dh_result.get('name')
                            )
                        )
        return resp_msgs

    def tag_buffer(self, tag):
        """
        Convenience method to tag the buffer version.
        """
        buffer_rev_id = self.get_revision_id(BUFFER)
        if buffer_rev_id is None:
            raise AppError(
                title='Unable to tag buffer as {}'.format(tag),
                description=('Buffer revision id could not be determined from'
                             'Deckhand'),
                status=falcon.HTTP_500,
                retry=False)
        self.tag_revision(buffer_rev_id, tag)

    def tag_revision(self, revision_id, tag):
        """
        Tags the specified revision with the specified tag
        """
        self.deckhand.tag_revision(revision_id=revision_id, tag=tag)

    def add_collection(self, collection_id, document_string):
        """
        Triggers a call to Deckhand to add a collection(bucket)
        Documents are assumed to be a string input, not a
        collection.
        Returns the id of the buffer version.
        """
        try:
            self.deckhand.put_bucket(collection_id, document_string)
        except DocumentExistsElsewhereError as deee:
            LOG.info('Deckhand has rejected this input because an included '
                     'document exists in another bucket already')
            raise ApiError(
                title='Documents may not exist in more than one collection',
                description=deee.response_message,
                status=falcon.HTTP_409)
        except DeckhandRejectedInputError as drie:
            LOG.info('Deckhand has rejected this input because: %s',
                     drie.response_message)
            raise ApiError(
                title="Document(s) invalid syntax or otherwise unsuitable",
                description=drie.response_message)
        # reset the revision dict so it regenerates.
        self.revision_dict = None
        return self.get_revision_id(BUFFER)

    def check_intermediate_commit(self):

        # Initialize variable
        list_of_committed_rev = []

        try:
            # Get the list of all revisions present in Deckhand
            all_revisions = self.deckhand.get_revision_list()

        except NoRevisionsExistError:
            # the values of None/None/None/0 are fine
            pass

        except DeckhandResponseError as drex:
            raise AppError(
                title='Unable to retrieve revisions',
                description=(
                    'Deckhand has responded unexpectedly: {}:{}'.format(
                        drex.status_code, drex.response_message)),
                status=falcon.HTTP_500,
                retry=False)

        if all_revisions:
            # Get the list of 'committed' revisions
            for revision in all_revisions:
                if 'committed' in revision['tags']:
                    list_of_committed_rev.append(revision)

            # This is really applicable for scenarios where multiple
            # configdocs commits and site actions were performed. Hence
            # we should expect at least 2 'committed' revisions to be
            # present in deckhand.
            #
            # We will check the second last most recent committed revision
            # to see if a site-action has been executed on it
            if len(list_of_committed_rev) > 1:
                if (('site-action-success' and 'site-action-failure') not in
                        list_of_committed_rev[-2]['tags']):
                    return True

        return False

    def _get_ordered_versions(self, versions=None):
        """returns a list of ordered versions"""

        # Default ordering
        def_order = [SUCCESSFUL_SITE_ACTION,
                     LAST_SITE_ACTION,
                     COMMITTED,
                     BUFFER]

        # Defaults to COMMITTED and BUFFER
        if versions is None:
            versions = [COMMITTED, BUFFER]

        elif not len(versions) == 2:
            raise AppError(
                title='Incorrect number of versions for comparison',
                description=(
                    'User must pass in 2 valid versions for comparison'),
                status=falcon.HTTP_400,
                retry=False)

        elif versions[0] == versions[1]:
            raise AppError(
                title='Versions must be different for comparison',
                description=(
                    'Versions must be unique in order to perform comparison'),
                status=falcon.HTTP_400,
                retry=False)

        for version in versions:
            if version not in def_order:
                raise AppError(
                    title='Invalid version detected',
                    description=(
                        '{} is not a valid version, which include: '
                        '{}'.format(version, ', '.join(def_order))),
                    status=falcon.HTTP_400,
                    retry=False)

        # Higher index in the def_order list will mean that it is a newer
        # version. We will swap the order and sort the version if need be.
        if def_order.index(versions[0]) > def_order.index(versions[1]):
            ordered_versions = list(reversed(versions))
        else:
            ordered_versions = versions

        return ordered_versions

    def _get_versions_name_id(self, ordered_versions):

        # Get version id
        old_version_id = self.get_revision_id(ordered_versions[0])
        new_version_id = self.get_revision_id(ordered_versions[1])

        # Get revision name
        old_version_name = ordered_versions[0]
        new_version_name = ordered_versions[1]

        # Check that revision id of LAST_SITE_ACTION and SUCCESSFUL_SITE_ACTION
        # is not None
        for name, rev_id in [(old_version_name, old_version_id),
                             (new_version_name, new_version_id)]:
            if (name in [LAST_SITE_ACTION, SUCCESSFUL_SITE_ACTION] and
                    rev_id is None):
                raise AppError(
                    title='Version does not exist',
                    description='{} version does not exist'.format(name),
                    status=falcon.HTTP_404,
                    retry=False)

        # Set to 0 if there is no committed version
        if old_version_name == COMMITTED and old_version_id is None:
            old_version_id = 0
            new_version_id = self.get_revision_id(BUFFER) or 0

        # Set new_version_id if None
        if new_version_id is None:
            new_version_id = (
                self.get_revision_id(BUFFER) or old_version_id or 0)

        return (
            old_version_name, new_version_name, old_version_id, new_version_id)

#
# End of ConfigdocsHelper class
#


#
# functions for module.
#

def _get_validation_endpoints():
    # returns the list of validation endpoint supported
    val_ep = '{}/validatedesign'
    return [
        {
            'name': 'Drydock',
            'url': val_ep.format(get_endpoint(Endpoints.DRYDOCK))
        },
        {
            'name': 'Armada',
            'url': val_ep.format(get_endpoint(Endpoints.ARMADA))
        },
        {
            'name': 'Promenade',
            'url': val_ep.format(get_endpoint(Endpoints.PROMENADE))
        }
    ]


def _get_validation_threads(validation_endpoints, ctx, design_ref):
    # create a list of validation threads from the endpoints
    validation_threads = []
    for endpoint in validation_endpoints:
        # create a holder for things we need back from the threads
        response = {'response': None}
        exception = {'exception': None}
        validation_threads.append({
            'thread':
            threading.Thread(
                target=_get_validations_for_component,
                kwargs={
                    'url': endpoint['url'],
                    'design_reference': design_ref,
                    'response': response,
                    'exception': exception,
                    'context_marker': ctx.external_marker,
                    'thread_name': endpoint['name'],
                    'log_extra': {
                        'req_id': ctx.request_id,
                        'external_ctx': ctx.external_marker,
                        'user': ctx.user
                    }
                }),
            'name': endpoint['name'],
            'url': endpoint['url'],
            'response': response,
            'exception': exception
        })
    return validation_threads


def _get_validations_for_component(url, design_reference, response,
                                   exception, context_marker, thread_name,
                                   **kwargs):
    # Invoke the POST for validation
    try:
        headers = {
            'X-Context-Marker': context_marker,
            'X-Auth-Token': get_token(),
            'content-type': 'application/json'
        }

        http_resp = requests.post(
            url,
            headers=headers,
            data=design_reference,
            timeout=(
                CONF.requests_config.validation_connect_timeout,
                CONF.requests_config.validation_read_timeout))
        # 400 response is "valid" failure to validate. > 400 is a problem.
        if http_resp.status_code > 400:
            http_resp.raise_for_status()
        response_dict = http_resp.json()
        response['response'] = response_dict
    except Exception as ex:
        # catch anything exceptional as a failure to run validations
        unable_str = '{} unable to validate configdocs'.format(thread_name)
        LOG.error("%s. Exception follows.", unable_str)
        LOG.error(str(ex))
        response['response'] = {
            'details': {
                'messageList': [{
                    'message': unable_str,
                    'kind': 'SimpleMessage',
                    'error': True
                }, {
                    'message': str(ex),
                    'kind': 'SimpleMessage',
                    'error': True
                }]
            }
        }
        exception['exception'] = ex


def _generate_dh_val_msg(msg, dh_result_name):
    # Maps a deckhand validation response to a ValidationMessage.
    # Result name is used if the msg doesn't specify a name field.
    # Deckhand may provide the following fields:
    # 'validation_schema', 'schema_path', 'name', 'schema', 'path',
    # 'error_section', 'message'
    not_spec = 'not specified'
    if 'diagnostic' not in msg:
        # format path, error_section, validation_schema, and schema_path
        # into diagnostic
        msg['diagnostic'] = 'Section: {} at {} (schema {} at {})'.format(
            msg.get('error_section', not_spec),
            msg.get('path', not_spec),
            msg.get('validation_schema', not_spec),
            msg.get('schema_path', not_spec)
        )

    if 'documents' not in msg:
        msg['documents'] = [{
            'name': msg.get('name', not_spec),
            'schema': msg.get('schema', not_spec)
        }]
    return _generate_validation_message(
        msg,
        name=dh_result_name,
        error=True,
        level='Error',
        source='Deckhand'
    )


def _generate_validation_message(msg, **kwargs):
    # Special note about kwargs: the values provided via kwargs are used
    # as defaults, not overrides. Values in the msg will take precedence.
    #
    # Using a compatible message, transform it into a ValidationMessage.
    # By combining it with the default values passed via kwargs. The values
    # used from kwargs match the fields listed below.

    fields = ['message', 'error', 'name', 'documents', 'level', 'diagnostic',
              'source']
    if 'documents' not in kwargs:
        kwargs['documents'] = []
    valmsg = {}
    for key in fields:
        valmsg[key] = msg.get(key, kwargs.get(key, None))
    valmsg['kind'] = 'ValidationMessage'
    valmsg['level'] = (
        valmsg.get('level') or _error_to_level(
            valmsg.get('error'))
    )
    return valmsg


def _error_to_level(error):
    """Convert a boolean error field to 'Error' or 'Info' """
    if error:
        return 'Error'
    else:
        return 'Info'


def _format_validations_to_status(val_msgs, error_count):
    # Using a list of validation messages and an error count,
    # formulates and returns a status response dict

    status = 'Success'
    message = 'Validations succeeded'
    code = falcon.HTTP_200
    if error_count > 0:
        status = 'Failure'
        message = 'Validations failed'
        code = falcon.HTTP_400

    return {
        "kind": "Status",
        "apiVersion": "v1.0",
        "metadata": {},
        "status": status,
        "message": message,
        "reason": "Validation",
        "details": {
            "errorCount": error_count,
            "messageList": val_msgs,
        },
        "code": code
    }
