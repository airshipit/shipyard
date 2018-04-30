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
import falcon
from oslo_config import cfg

from shipyard_airflow import policy
from shipyard_airflow.control.configdocs import configdocs_helper
from shipyard_airflow.control.api_lock import (api_lock, ApiLockType)
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.control.configdocs.configdocs_helper import (
    ConfigdocsHelper)
from shipyard_airflow.errors import ApiError

CONF = cfg.CONF
VERSION_VALUES = ['buffer', 'committed']


class ConfigDocsStatusResource(BaseResource):
    """
    Configdocs Status handles the retrieval of the configuration documents'
    statuses
    """

    @policy.ApiEnforcer('workflow_orchestrator:get_configdocs_status')
    def on_get(self, req, resp):
        """Returns a list of the configdocs and their statuses"""
        helper = ConfigdocsHelper(req.context)
        resp.body = self.to_json(helper.get_configdocs_status())
        resp.status = falcon.HTTP_200


class ConfigDocsResource(BaseResource):
    """
    Configdocs handles the creation and retrieval of configuration
    documents into Shipyard.
    """

    @policy.ApiEnforcer('workflow_orchestrator:create_configdocs')
    @api_lock(ApiLockType.CONFIGDOCS_UPDATE)
    def on_post(self, req, resp, collection_id):
        """
        Ingests a collection of documents
        """
        content_length = req.content_length or 0
        if (content_length == 0):
            raise ApiError(
                title=('Content-Length is a required header'),
                description='Content Length is 0 or not specified',
                status=falcon.HTTP_400,
                error_list=[{
                    'message': (
                        'The Content-Length specified is 0 or not set. Check '
                        'that a valid payload is included with this request '
                        'and that your client is properly including a '
                        'Content-Length header. Note that a newline character '
                        'in a prior header can trigger subsequent headers to '
                        'be ignored and trigger this failure.')
                }],
                retry=False, )
        document_data = req.stream.read(content_length)

        buffer_mode = req.get_param('buffermode')

        helper = ConfigdocsHelper(req.context)
        validations = self.post_collection(
            helper=helper,
            collection_id=collection_id,
            document_data=document_data,
            buffer_mode_param=buffer_mode)

        resp.location = '/api/v1.0/configdocs/{}'.format(collection_id)
        resp.body = self.to_json(validations)
        resp.status = falcon.HTTP_201

    @policy.ApiEnforcer('workflow_orchestrator:get_configdocs')
    def on_get(self, req, resp, collection_id):
        """
        Returns a collection of documents
        """
        version = (req.params.get('version') or 'buffer')
        self._validate_version_parameter(version)
        helper = ConfigdocsHelper(req.context)
        # Not reformatting to JSON or YAML since just passing through
        resp.body = self.get_collection(
            helper=helper, collection_id=collection_id, version=version)
        resp.append_header('Content-Type', 'application/x-yaml')
        resp.status = falcon.HTTP_200

    def _validate_version_parameter(self, version):
        # performs validation of version parameter
        if version.lower() not in VERSION_VALUES:
            raise ApiError(
                title='Invalid version query parameter specified',
                description=(
                    'version must be {}'.format(', '.join(VERSION_VALUES))),
                status=falcon.HTTP_400,
                retry=False, )

    def get_collection(self, helper, collection_id, version='buffer'):
        """
        Attempts to retrieve the specified collection of documents
        either from the buffer or committed version, as specified
        """
        return helper.get_collection_docs(version, collection_id)

    def post_collection(self,
                        helper,
                        collection_id,
                        document_data,
                        buffer_mode_param=None):
        """
        Ingest the collection after checking preconditions
        """
        buffer_mode = ConfigdocsHelper.get_buffer_mode(buffer_mode_param)

        if helper.is_buffer_valid_for_bucket(collection_id, buffer_mode):
            buffer_revision = helper.add_collection(collection_id,
                                                    document_data)
            if helper.is_collection_in_buffer(collection_id):
                return helper.get_deckhand_validation_status(buffer_revision)
            else:
                raise ApiError(
                    title=('Collection {} not added to Shipyard '
                           'buffer'.format(collection_id)),
                    description='Collection empty or resulted in no revision',
                    status=falcon.HTTP_400,
                    error_list=[{
                        'message': (
                            'Empty collections are not supported. After '
                            'processing, the collection {} added no new '
                            'revision, and has been rejected as invalid '
                            'input'.format(collection_id))
                    }],
                    retry=False,
                )
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


class CommitConfigDocsResource(BaseResource):
    """
    Commits the buffered configdocs, if the validations pass (or are
    overridden (force = true))
    Returns the list of validations.
    """

    unable_to_commmit = 'Unable to commit configuration documents'

    @policy.ApiEnforcer('workflow_orchestrator:commit_configdocs')
    @api_lock(ApiLockType.CONFIGDOCS_UPDATE)
    def on_post(self, req, resp):
        """
        Get validations from all UCP components
        Functionality does not exist yet
        """
        # force and dryrun query parameter is False unless explicitly true
        force = req.get_param_as_bool(name='force') or False
        dryrun = req.get_param_as_bool(name='dryrun') or False
        helper = ConfigdocsHelper(req.context)
        validations = self.commit_configdocs(helper, force, dryrun)
        resp.body = self.to_json(validations)
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
        validations = helper.get_validations_for_buffer()
        if dryrun:
            validations['code'] = falcon.HTTP_200
            if 'message' in validations:
                validations['message'] = (
                    validations['message'] + ' DRYRUN')
            else:
                validations['message'] = 'DRYRUN'
        else:
            if force or validations.get('status') == 'Success':
                helper.tag_buffer(configdocs_helper.COMMITTED)
            if force and validations.get('status') == 'Failure':
                # override the status in the response
                validations['code'] = falcon.HTTP_200
                if 'message' in validations:
                    validations['message'] = (
                        validations['message'] + ' FORCED SUCCESS')
                else:
                    validations['message'] = 'FORCED SUCCESS'
        return validations
