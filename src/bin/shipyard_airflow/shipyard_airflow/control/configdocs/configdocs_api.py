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
Resources representing the configdocs API for shipyard
"""
import logging

import falcon
from oslo_config import cfg

from shipyard_airflow import policy
from shipyard_airflow.control.api_lock import (api_lock, ApiLockType)
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.control.helpers import configdocs_helper
from shipyard_airflow.control.helpers.configdocs_helper import (
    ConfigdocsHelper, add_messages_to_validation_status)
from shipyard_airflow.errors import ApiError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
VERSION_VALUES = [
    'buffer', 'committed', 'last_site_action', 'successful_site_action'
]
DEPLOYMENT_DATA_DOC = {
    'name': CONF.document_info.deployment_version_name,
    'schema': CONF.document_info.deployment_version_schema
}


class ConfigDocsStatusResource(BaseResource):
    """
    Configdocs Status handles the retrieval of the configuration documents'
    statuses
    """

    @policy.ApiEnforcer(policy.GET_CONFIGDOCS_STATUS)
    def on_get(self, req, resp):
        """Returns a list of the configdocs and their statuses"""
        versions = req.params.get('versions') or None
        helper = ConfigdocsHelper(req.context)
        resp.text = self.to_json(helper.get_configdocs_status(versions))
        resp.status = falcon.HTTP_200


class ConfigDocsResource(BaseResource):
    """
    Configdocs handles the creation and retrieval of configuration
    documents into Shipyard.
    """

    @policy.ApiEnforcer(policy.CREATE_CONFIGDOCS)
    @api_lock(ApiLockType.CONFIGDOCS_UPDATE)
    def on_post(self, req, resp, collection_id):
        """
        Ingests a collection of documents
        """
        # Determine if this request is clearing the collection's contents.
        empty_coll = req.get_param_as_bool('empty-collection') or False
        if empty_coll:
            document_data = ""
            LOG.debug("Collection %s is being emptied", collection_id)
        else:
            # Note, a newline in a prior header can trigger subsequent
            # headers to be "missing" (and hence cause this code to think
            # that the content length is missing)
            content_length = self.validate_content_length(req.content_length)
            document_data = req.stream.read(content_length)

        buffer_mode = req.get_param('buffermode')

        helper = ConfigdocsHelper(req.context)
        validations = self.post_collection(helper=helper,
                                           collection_id=collection_id,
                                           document_data=document_data,
                                           buffer_mode_param=buffer_mode,
                                           empty_collection=empty_coll)

        resp.status = falcon.HTTP_201
        if validations and validations['status'] == 'Success':
            validations['code'] = resp.status
        resp.location = '/api/v1.0/configdocs/{}'.format(collection_id)
        resp.text = self.to_json(validations)

    def validate_content_length(self, content_length):
        """Validates that the content length header is valid

        :param content_length: the value of the content-length header.
        :returns: the validate content length value
        """
        content_length = content_length or 0
        if (content_length == 0):
            raise ApiError(
                title=('Content-Length is a required header'),
                description='Content Length is 0 or not specified',
                status=falcon.HTTP_400,
                error_list=[{
                    'message':
                    ("The Content-Length specified is 0 or not set. To "
                     "clear a collection's contents, please specify "
                     "the query parameter 'empty-collection=true'."
                     "Otherwise, a non-zero length payload and "
                     "matching Content-Length header is required to "
                     "post a collection.")
                }],
                retry=False,
            )
        return content_length

    @policy.ApiEnforcer(policy.GET_CONFIGDOCS)
    def on_get(self, req, resp, collection_id):
        """
        Returns a collection of documents
        """
        version = (req.params.get('version') or 'buffer')
        cleartext_secrets = req.get_param_as_bool('cleartext-secrets') or False
        self._validate_version_parameter(version)
        helper = ConfigdocsHelper(req.context)

        # Check access to cleartext_secrets
        if cleartext_secrets:
            policy.check_auth(req.context, policy.GET_CONFIGDOCS_CLRTXT)

        # Not reformatting to JSON or YAML since just passing through
        resp.text = self.get_collection(helper=helper,
                                        collection_id=collection_id,
                                        version=version,
                                        cleartext_secrets=cleartext_secrets)
        resp.append_header('Content-Type', 'application/x-yaml')
        resp.status = falcon.HTTP_200

    def _validate_version_parameter(self, version):
        # performs validation of version parameter
        if version.lower() not in VERSION_VALUES:
            raise ApiError(
                title='Invalid version query parameter specified',
                description=('version must be {}'.format(
                    ', '.join(VERSION_VALUES))),
                status=falcon.HTTP_400,
                retry=False,
            )

    def get_collection(self,
                       helper,
                       collection_id,
                       version='buffer',
                       cleartext_secrets=False):
        """
        Attempts to retrieve the specified collection of documents
        either from the buffer, committed version, last site action
        or successful site action, as specified
        """
        return helper.get_collection_docs(version, collection_id,
                                          cleartext_secrets)

    def _validate_deployment_version(self, helper, document_data):
        """
        Validate that the received documents include a deployment version doc.
        This function should only be called if needed, and will not do any
        checking to see if shipyard is configured to skip this check.
        Return True if the deployment version doc is present, False otherwise.
        """
        LOG.info("Validating deployment data")
        LOG.debug("Searching for schema: %s and name: %s",
                  DEPLOYMENT_DATA_DOC['schema'], DEPLOYMENT_DATA_DOC['name'])
        return helper.check_for_document(document_data,
                                         DEPLOYMENT_DATA_DOC['name'],
                                         DEPLOYMENT_DATA_DOC['schema'])

    def post_collection(self,
                        helper,
                        collection_id,
                        document_data,
                        buffer_mode_param=None,
                        empty_collection=False):
        """Ingest the collection after checking preconditions"""
        extra_messages = {'warning': [], 'info': []}
        validation_status = None
        buffer_mode = ConfigdocsHelper.get_buffer_mode(buffer_mode_param)

        # Validate that a deployment version document was provided, unless we
        # were told to skip this check
        ver_validation_cfg = CONF.validations.deployment_version_create.lower()
        if empty_collection or ver_validation_cfg == 'skip':
            LOG.debug('Skipping deployment version document validation')
        else:
            if not self._validate_deployment_version(helper, document_data):
                title = 'Deployment version document missing from collection'
                error_msg = ('Expected document to be present with schema: {} '
                             'and name: {}').format(
                                 DEPLOYMENT_DATA_DOC['schema'],
                                 DEPLOYMENT_DATA_DOC['name'])

                if ver_validation_cfg in ['info', 'warning']:
                    extra_messages[ver_validation_cfg].append('{}. {}'.format(
                        title, error_msg))
                else:  # Error
                    raise ApiError(
                        title=title,
                        description=('Collection rejected due to missing '
                                     'deployment data document'),
                        status=falcon.HTTP_400,
                        error_list=[{
                            'message': error_msg
                        }],
                        retry=False,
                    )

        if helper.is_buffer_valid_for_bucket(collection_id, buffer_mode):
            buffer_revision = helper.add_collection(collection_id,
                                                    document_data)
            if not (empty_collection or
                    helper.is_collection_in_buffer(collection_id)):
                # raise an error if adding the collection resulted in no new
                # revision (meaning it was unchanged) and we're not explicitly
                # clearing the collection
                raise ApiError(
                    title=('Collection {} not added to Shipyard '
                           'buffer'.format(collection_id)),
                    description='Collection created no new revision',
                    status=falcon.HTTP_400,
                    error_list=[{
                        'message':
                        ('The collection {} added no new revision, and has '
                         'been rejected as invalid input. This likely '
                         'means that the collection already exists and '
                         'was reloaded with the same contents'.format(
                             collection_id))
                    }],
                    retry=False,
                )
            else:
                validation_status = helper.get_deckhand_validation_status(
                    buffer_revision)
        else:
            raise ApiError(
                title='Invalid collection specified for buffer',
                description='Buffermode : {}'.format(buffer_mode.value),
                status=falcon.HTTP_409,
                error_list=[{
                    'message': ('Buffer is either not empty or the '
                                'collection already exists in buffer. '
                                'Setting a different buffermode may '
                                'provide the desired functionality')
                }],
                retry=False,
            )

        for level, messages in extra_messages.items():
            if len(messages):
                add_messages_to_validation_status(validation_status, messages,
                                                  level)
        return validation_status


class CommitConfigDocsResource(BaseResource):
    """
    Commits the buffered configdocs, if the validations pass (or are
    overridden (force = true))
    Returns the list of validations.
    """

    unable_to_commmit = 'Unable to commit configuration documents'

    @policy.ApiEnforcer(policy.COMMIT_CONFIGDOCS)
    @api_lock(ApiLockType.CONFIGDOCS_UPDATE)
    def on_post(self, req, resp):
        """
        Get validations from all Airship components
        Functionality does not exist yet
        """
        # force and dryrun query parameter is False unless explicitly true
        force = req.get_param_as_bool(name='force') or False
        dryrun = req.get_param_as_bool(name='dryrun') or False
        helper = ConfigdocsHelper(req.context)
        validations = self.commit_configdocs(helper, force, dryrun)
        resp.text = self.to_json(validations)
        resp.status = validations.get('code', falcon.HTTP_200)

    def commit_configdocs(self, helper, force, dryrun):
        """
        Attempts to commit the configdocs
        """
        if helper.is_buffer_empty():
            raise ApiError(
                title=CommitConfigDocsResource.unable_to_commmit,
                description='There are no documents in the buffer to commit',
                status=falcon.HTTP_409,
                retry=True)
        validations = helper.get_validations_for_revision(
            helper.get_revision_id(configdocs_helper.BUFFER))
        if dryrun:
            validations['code'] = falcon.HTTP_200
            if 'message' in validations:
                validations['message'] = (validations['message'] + ' DRYRUN')
            else:
                validations['message'] = 'DRYRUN'
        else:
            if force or validations.get('status') == 'Success':
                helper.tag_buffer(configdocs_helper.COMMITTED)
            if force and validations.get('status') == 'Failure':
                # override the status in the response
                validations['code'] = falcon.HTTP_200
                if 'message' in validations:
                    validations['message'] = (validations['message'] +
                                              ' FORCED SUCCESS')
                else:
                    validations['message'] = 'FORCED SUCCESS'
        return validations
