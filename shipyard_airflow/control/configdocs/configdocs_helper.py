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
import json
import logging
import threading

import falcon
from oslo_config import cfg
import requests

from shipyard_airflow.control.configdocs.deckhand_client import (
    DeckhandClient,
    DeckhandPaths,
    DeckhandRejectedInputError,
    DeckhandResponseError,
    DocumentExistsElsewhereError,
    NoRevisionsExistError
)
from shipyard_airflow.control.service_endpoints import (
    Endpoints,
    get_endpoint,
    get_token
)
from shipyard_airflow.errors import ApiError, AppError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

# keys for the revision dict, and consistency of strings for committed
# and buffer.
COMMITTED = 'committed'
BUFFER = 'buffer'
LATEST = 'latest'
REVISION_COUNT = 'count'

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

    def __init__(self, context_marker):
        """
        Sets up this Configdocs helper with the supplied
        context marker
        """
        self.deckhand = DeckhandClient(context_marker)
        self.context_marker = context_marker
        # The revision_dict indicates the revisions that are
        # associated with the buffered and committed doc sets. There
        # is a risk of this being out of sync if there is high volume
        # of commits and adds of docs going on in parallel, but not
        # really much more than if this data is used in subsequent
        # statements following a call within a method.
        self.revision_dict = None

    @staticmethod
    def get_buffer_mode(buffermode_string):
        """
        Checks the buffer mode for valid values.
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
        return self._get_buffer_revision() is None

    def is_collection_in_buffer(self, collection_id):
        """
        Returns if the collection is represented in the buffer
        """
        if self.is_buffer_empty():
            return False

        # If there is no committed revision, then it's 0.
        # new revision is ok because we just checked for buffer emptiness
        old_revision_id = self._get_committed_rev_id()
        if old_revision_id is None:
            old_revision_id = 0
        try:
            diff = self.deckhand.get_diff(
                old_revision_id=old_revision_id,
                new_revision_id=self._get_buffer_rev_id()
            )
            # the collection is in the buffer if it's not unmodified
            return diff.get(collection_id, 'unmodified') != 'unmodified'
        except DeckhandResponseError as drex:
            raise AppError(
                title='Unable to retrieve revisions',
                description=(
                    'Deckhand has responded unexpectedly: {}:{}'.format(
                        drex.status_code,
                        drex.response_message
                    )
                ),
                status=falcon.HTTP_500,
                retry=False,
            )

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
            committed_rev = self._get_committed_revision()
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

    def _get_revision_dict(self):
        """
        Returns a dictionary with values representing the revisions in
        Deckhand that Shipyard cares about - committed, buffer,
        and latest, as well as a count of revisions
        Committed and buffer are revisions associated with the
        shipyard tags. If either of those are not present in deckhand,
        returns None for the value.
        Latest holds the revision information for the newest revision.
        """
        # return the cached instance version of the revision dict.
        if self.revision_dict is not None:
            return self.revision_dict
        # or generate one for the cache
        committed_revision = None
        buffer_revision = None
        latest_revision = None
        revision_count = 0
        try:
            revisions = self.deckhand.get_revision_list()
            revision_count = len(revisions)
            if revisions:
                latest_revision = revisions[-1]
                for revision in reversed(revisions):
                    tags = revision.get('tags', [])
                    if COMMITTED in tags or ROLLBACK_COMMIT in tags:
                        committed_revision = revision
                        break
                    else:
                        # there are buffer revisions, only grab it on
                        # the first pass through
                        # if the first revision is committed, or if there
                        # are no revsisions, buffer revsision stays None
                        if buffer_revision is None:
                            buffer_revision = revision
        except NoRevisionsExistError:
            # the values of None/None/None/0 are fine
            pass
        except DeckhandResponseError as drex:
            raise AppError(
                title='Unable to retrieve revisions',
                description=(
                    'Deckhand has responded unexpectedly: {}:{}'.format(
                        drex.status_code,
                        drex.response_message
                    )
                ),
                status=falcon.HTTP_500,
                retry=False,
            )
        self.revision_dict = {
            COMMITTED: committed_revision,
            BUFFER: buffer_revision,
            LATEST: latest_revision,
            REVISION_COUNT: revision_count
        }
        return self.revision_dict

    def _get_buffer_revision(self):
        # convenience helper to drill down to Buffer revision
        return self._get_revision_dict().get(BUFFER)

    def _get_buffer_rev_id(self):
        # convenience helper to drill down to Buffer revision id
        buf_rev = self._get_revision_dict().get(BUFFER)
        return buf_rev['id'] if buf_rev else None

    def _get_latest_revision(self):
        # convenience helper to drill down to latest revision
        return self._get_revision_dict().get(LATEST)

    def _get_latest_rev_id(self):
        # convenience helper to drill down to latest revision id
        latest_rev = self._get_revision_dict().get(LATEST)
        return latest_rev['id'] if latest_rev else None

    def _get_committed_revision(self):
        # convenience helper to drill down to committed revision
        return self._get_revision_dict().get(COMMITTED)

    def _get_committed_rev_id(self):
        # convenience helper to drill down to committed revision id
        committed_rev = self._get_revision_dict().get(COMMITTED)
        return committed_rev['id'] if committed_rev else None

    def get_collection_docs(self, version, collection_id):
        """
        Returns the requested collection of docs based on the version
        specifier. Since the default is the buffer, only return
        committed if explicitly stated. No need to further check the
        parameter for validity here.
        """
        LOG.info('Retrieving collection %s from %s', collection_id, version)
        if version == COMMITTED:
            return self._get_committed_docs(collection_id)
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
            buffer_id = self._get_buffer_rev_id()
            return self.deckhand.get_docs_from_revision(
                revision_id=buffer_id,
                bucket_id=collection_id
            )
        raise ApiError(
            title='No documents to retrieve',
            description=('The Shipyard buffer is empty or does not contain '
                         'this collection'),
            status=falcon.HTTP_404,
            retry=False,
        )

    def _get_committed_docs(self, collection_id):
        """
        Returns the collection if it exists as committed.
        """
        committed_id = self._get_committed_rev_id()
        if committed_id:
            return self.deckhand.get_docs_from_revision(
                revision_id=committed_id,
                bucket_id=collection_id
            )
        # if there is no committed...
        raise ApiError(
            title='No documents to retrieve',
            description='There is no committed version of this collection',
            status=falcon.HTTP_404,
            retry=False,
        )

    def get_rendered_configdocs(self, version=BUFFER):
        """
        Returns the rendered configuration documents for the specified
        revision (by name BUFFER, COMMITTED)
        """
        revision_dict = self._get_revision_dict()
        if version in (BUFFER, COMMITTED):
            if revision_dict.get(version):
                revision_id = revision_dict.get(version).get('id')
                return self.deckhand.get_rendered_docs_from_revision(
                    revision_id=revision_id
                )
            else:
                raise ApiError(
                    title='This revision does not exist',
                    description='{} version does not exist'.format(version),
                    status=falcon.HTTP_404,
                    retry=False,
                )

    def get_validations_for_buffer(self):
        """
        Convenience method to do validations for buffer version.
        """
        buffer_rev_id = self._get_buffer_rev_id()
        if buffer_rev_id:
            return self.get_validations_for_revision(buffer_rev_id)
        raise AppError(
            title='Unable to start validation of buffer',
            description=('Buffer revision id could not be determined from'
                         'Deckhand'),
            status=falcon.HTTP_500,
            retry=False,
        )

    @staticmethod
    def _get_design_reference(revision_id):
        # Constructs the design reference as json for use by other components
        design_reference = {
            "rel": "design",
            "href": "deckhand+{}/rendered-documents".format(
                DeckhandPaths.RENDERED_REVISION_DOCS.value.format(revision_id)
            ),
            "type": "application/x-yaml"
        }
        return json.dumps(design_reference)

    @staticmethod
    def _get_validation_endpoints():
        # returns the list of validation endpoint supported
        val_ep = '{}/validatedesign'
        return [
            {'name': 'Drydock',
             'url': val_ep.format(get_endpoint(Endpoints.DRYDOCK))},
            {'name': 'Armada',
             'url': val_ep.format(get_endpoint(Endpoints.ARMADA))},
        ]

    @staticmethod
    def _get_validation_threads(validation_endpoints,
                                revision_id,
                                context_marker):
        # create a list of validation threads from the endpoints
        validation_threads = []
        for endpoint in validation_endpoints:
            # create a holder for things we need back from the threads
            response = {'response': None}
            exception = {'exception': None}
            validation_threads.append(
                {
                    'thread': threading.Thread(
                        target=ConfigdocsHelper._get_validations_for_component,
                        args=(
                            endpoint['url'],
                            ConfigdocsHelper._get_design_reference(
                                revision_id
                            ),
                            response,
                            exception,
                            context_marker
                        )
                    ),
                    'name': endpoint['name'],
                    'url': endpoint['url'],
                    'response': response,
                    'exception': exception
                }
            )
        return validation_threads

    @staticmethod
    def _get_validations_for_component(url,
                                       design_reference,
                                       response,
                                       exception,
                                       context_marker):
        # Invoke the POST for validation
        try:
            headers = {
                'X-Context-Marker': context_marker,
                'X-Auth-Token': get_token(),
                'content-type': 'application/x-yaml'
            }

            http_resp = requests.post(url,
                                      headers=headers,
                                      data=design_reference,
                                      timeout=(5, 30))
            http_resp.raise_for_status()
            raw_response = http_resp.decode('utf-8')
            response_dict = json.loads(raw_response)
            response['response'] = response_dict
        except Exception as ex:
            # catch anything exceptional as a failure to validate
            LOG.error(ex)
            exception['exception'] = ex

    def get_validations_for_revision(self, revision_id):
        """
        Use the endpoints for each of the UCP components to validate the
        version indicated. Uses:
        https://github.com/att-comdev/ucp-integration/blob/master/docs/api-conventions.md#post-v10validatedesign
        format.
        """
        resp_msgs = []

        validation_threads = ConfigdocsHelper._get_validation_threads(
            ConfigdocsHelper._get_validation_endpoints(),
            revision_id,
            self.context_marker
        )
        # trigger each validation in parallel
        for validation_thread in validation_threads:
            if validation_thread.get('thread'):
                validation_thread.get('thread').start()
        # wait for all validations to return
        for validation_thread in validation_threads:
            validation_thread.get('thread').join()

        # check on the response, extract the validations
        error_count = 0
        for validation_thread in validation_threads:
            val_response = validation_thread.get('response')['response']
            if (not val_response or
                    validation_thread.get('exception')['exception']):
                # exception was raised, or no body was returned.
                raise AppError(
                    title='Unable to properly validate configdocs',
                    description=(
                        'Invocation of validation by {} has failed'.format(
                            validation_thread.get('name')
                        )
                    ),
                    status=falcon.HTTP_500,
                    retry=False,
                )
            if not val_response:
                raise AppError(
                    title='An invalid response was returned by validation',
                    description='No valid response status from {}'.format(
                        validation_thread.get('name')),
                    status=falcon.HTTP_500,
                    retry=False,
                )
            # invalid status needs collection of messages
            # valid status means that it passed. No messages to collect
            msg_list = val_response.get('details').get('messageList')
            for msg in msg_list:
                if msg.get('error'):
                    error_count = error_count + 1
                    resp_msgs.append(
                        {
                            'name': validation_thread.get('name'),
                            'message': msg.get('message'),
                            'error': True
                        }
                    )
                else:
                    resp_msgs.append(
                        {
                            'name': validation_thread.get('name'),
                            'message': msg.get('message'),
                            'error': False
                        }
                    )
        # Deckhand does it differently. Incorporate those validation
        # failures
        dh_validations = self._get_deckhand_validations(revision_id)
        error_count += len(dh_validations)
        resp_msgs.extend(dh_validations)
        # return the formatted status response
        return ConfigdocsHelper._format_validations_to_status(
            resp_msgs,
            error_count
        )

    def get_deckhand_validation_status(self, revision_id):
        """
        Returns the status object representing the deckhand validation
        results
        """
        dh_validations = self._get_deckhand_validations(revision_id)
        error_count = len(dh_validations)
        return ConfigdocsHelper._format_validations_to_status(
            dh_validations,
            error_count
        )

    def _get_deckhand_validations(self, revision_id):
        # Returns any validations that deckhand has on hand for this
        # revision.
        resp_msgs = []
        deckhand_val = self.deckhand.get_all_revision_validations(revision_id)
        if deckhand_val.get('results'):
            for dh_result in deckhand_val.get('results'):
                if dh_result.get('errors'):
                    for error in dh_result.get('errors'):
                        resp_msgs.append(
                            {
                                'name': dh_result.get('name'),
                                'message': error.get('message'),
                                'error': True
                            }
                        )
        return resp_msgs

    @staticmethod
    def _format_validations_to_status(val_msgs, error_count):
        # Using a list of validation messages and an error count,
        # formulates and returns a status response dict

        status = 'Valid'
        message = 'Validations succeeded'
        code = falcon.HTTP_200
        if error_count > 0:
            status = 'Invalid'
            message = 'Validations failed'
            code = falcon.HTTP_400

        return {
            "kind": "Status",
            "apiVersion": "v1",
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

    def tag_buffer(self, tag):
        """
        Convenience method to tag the buffer version.
        """
        buffer_rev_id = self._get_buffer_rev_id()
        if buffer_rev_id is None:
            raise AppError(
                title='Unable to tag buffer as {}'.format(tag),
                description=('Buffer revision id could not be determined from'
                             'Deckhand'),
                status=falcon.HTTP_500,
                retry=False,
            )
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
                status=falcon.HTTP_409
            )
        except DeckhandRejectedInputError as drie:
            LOG.info('Deckhand has rejected this input because: %s',
                     drie.response_message)
            raise ApiError(
                title="Document(s) invalid syntax or otherwise unsuitable",
                description=drie.response_message,
            )
        # reset the revision dict so it regenerates.
        self.revision_dict = None
        return self._get_buffer_rev_id()
