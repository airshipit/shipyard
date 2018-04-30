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
""" Tests for the configdocs_api"""
import json
import mock
from mock import ANY, patch

import pytest

from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.control.configdocs.configdocs_api import (
    CommitConfigDocsResource,
    ConfigDocsResource
)
from shipyard_airflow.control.configdocs.configdocs_helper import \
    ConfigdocsHelper
from shipyard_airflow.control.api_lock import ApiLock
from shipyard_airflow.errors import ApiError
from tests.unit.control import common

CTX = ShipyardRequestContext()


class TestConfigDocsStatusResource():
    @patch.object(ConfigdocsHelper, 'get_configdocs_status',
                  common.str_responder)
    def test_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        result = api_client.simulate_get(
            "/api/v1.0/configdocs", headers=common.AUTH_HEADERS)
        assert result.status_code == 200
        assert result.text == json.dumps(common.str_responder(), default=str)
        assert result.headers[
            'content-type'] == 'application/json; charset=UTF-8'


class TestConfigDocsResource():
    @patch.object(ConfigDocsResource, 'post_collection', common.str_responder)
    @mock.patch.object(ApiLock, 'release')
    @mock.patch.object(ApiLock, 'acquire')
    def test_on_post_empty(self, mock_acquire, mock_release, api_client):
        result = api_client.simulate_post(
            "/api/v1.0/configdocs/coll1", headers=common.AUTH_HEADERS)
        assert result.status_code == 400
        assert 'Content-Length specified is 0 or not set' in result.text

    @patch.object(ConfigDocsResource, 'post_collection', common.str_responder)
    @mock.patch.object(ApiLock, 'release')
    @mock.patch.object(ApiLock, 'acquire')
    def test_on_post(self, mock_acquire, mock_release, api_client):
        headers = {'Content-Length': '1'}
        headers.update(common.AUTH_HEADERS)
        result = api_client.simulate_post(
            "/api/v1.0/configdocs/coll1", headers=headers, body='A')
        assert result.status_code == 201

    @patch.object(ConfigDocsResource, 'get_collection', common.str_responder)
    def test_configdocs_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        result = api_client.simulate_get("/api/v1.0/configdocs/coll1",
                                         headers=common.AUTH_HEADERS)
        assert result.status_code == 200

    def test__validate_version_parameter(self):
        """
        test of the version parameter validation
        """
        cdr = ConfigDocsResource()
        with pytest.raises(ApiError):
            cdr._validate_version_parameter('asdfjkl')

        for version in ('buffer', 'committed'):
            try:
                cdr._validate_version_parameter(version)
            except ApiError:
                # should not raise an exception.
                assert False

    def test_get_collection(self):
        helper = None
        with patch.object(
                ConfigdocsHelper, 'get_collection_docs') as mock_method:
            cdr = ConfigDocsResource()
            helper = ConfigdocsHelper(CTX)
            cdr.get_collection(helper, 'apples')

        mock_method.assert_called_once_with('buffer', 'apples')

    @patch.object(ConfigdocsHelper, 'is_collection_in_buffer',
                  lambda x, y: True)
    def test_post_collection(self):
        """
        Tests the post collection method of the ConfigdocsResource
        """
        helper = None
        collection_id = 'trees'
        document_data = 'lots of info'
        with patch.object(ConfigdocsHelper, 'add_collection') as mock_method:
            cdr = ConfigDocsResource()
            helper = ConfigdocsHelper(CTX)
            helper.is_buffer_valid_for_bucket = lambda a, b: True
            helper.get_deckhand_validation_status = (
                lambda a: ConfigdocsHelper._format_validations_to_status([], 0)
            )
            cdr.post_collection(helper=helper,
                                collection_id=collection_id,
                                document_data=document_data)

        mock_method.assert_called_once_with(collection_id, document_data)

    @patch.object(ConfigdocsHelper, 'is_collection_in_buffer',
                  lambda x, y: True)
    @patch.object(ConfigdocsHelper, 'is_buffer_valid_for_bucket',
                  lambda x, y, z: False)
    def test_post_collection_not_valid_for_buffer(self):
        """
        Tests the post collection method of the ConfigdocsResource
        """
        helper = None
        collection_id = 'trees'
        document_data = 'lots of info'
        with pytest.raises(ApiError) as apie:
            cdr = ConfigDocsResource()
            helper = ConfigdocsHelper(CTX)
            # not valid for bucket
            helper.get_deckhand_validation_status = (
                lambda a: ConfigdocsHelper._format_validations_to_status([], 0)
            )
            cdr.post_collection(helper=helper,
                                collection_id=collection_id,
                                document_data=document_data)
        assert apie.value.status == '409 Conflict'

    @patch.object(ConfigdocsHelper, 'is_collection_in_buffer',
                  lambda x, y: False)
    @patch.object(ConfigdocsHelper, 'is_buffer_valid_for_bucket',
                  lambda x, y, z: True)
    def test_post_collection_not_added(self):
        """
        Tests the post collection method of the ConfigdocsResource
        """
        helper = None
        collection_id = 'trees'
        document_data = 'lots of info'
        with patch.object(ConfigdocsHelper, 'add_collection') as mock_method:
            cdr = ConfigDocsResource()
            helper = ConfigdocsHelper(CTX)
            helper.get_deckhand_validation_status = (
                lambda a: ConfigdocsHelper._format_validations_to_status([], 0)
            )
            with pytest.raises(ApiError) as apie:
                cdr.post_collection(helper=helper,
                                    collection_id=collection_id,
                                    document_data=document_data)

            assert apie.value.status == '400 Bad Request'
        mock_method.assert_called_once_with(collection_id, document_data)


class TestCommitConfigDocsResource():
    @mock.patch.object(ApiLock, 'release')
    @mock.patch.object(ApiLock, 'acquire')
    def test_on_post(self, mock_acquire, mock_release, api_client):
        queries = ["", "force=true", "dryrun=true"]
        with patch.object(
            CommitConfigDocsResource, 'commit_configdocs', return_value={}
        ) as mock_method:
            for q in queries:
                result = api_client.simulate_post(
                    "/api/v1.0/commitconfigdocs", query_string=q,
                    headers=common.AUTH_HEADERS)
                assert result.status_code == 200
        mock_method.assert_has_calls([
            mock.call(ANY, False, False),
            mock.call(ANY, True, False),
            mock.call(ANY, False, True)
        ])

    def test_commit_configdocs(self):
        """
        Tests the CommitConfigDocsResource method commit_configdocs
        """
        ccdr = CommitConfigDocsResource()
        commit_resp = None
        with patch.object(ConfigdocsHelper, 'tag_buffer') as mock_method:
            helper = ConfigdocsHelper(CTX)
            helper.is_buffer_empty = lambda: False
            helper.get_validations_for_buffer = lambda: {'status': 'Success'}
            commit_resp = ccdr.commit_configdocs(helper, False, False)

        mock_method.assert_called_once_with('committed')
        assert commit_resp['status'] == 'Success'

        commit_resp = None
        with patch.object(ConfigdocsHelper, 'tag_buffer') as mock_method:
            helper = ConfigdocsHelper(CTX)
            helper.is_buffer_empty = lambda: False
            helper.get_validations_for_buffer = (
                lambda: {
                    'status': 'Failure',
                    'code': '400 Bad Request',
                    'message': 'this is a mock response'
                }
            )
            commit_resp = ccdr.commit_configdocs(helper, False, False)
        assert '400' in commit_resp['code']
        assert commit_resp['message'] is not None
        assert commit_resp['status'] == 'Failure'

    def test_commit_configdocs_force(self):
        """
        Tests the CommitConfigDocsResource method commit_configdocs
        """
        ccdr = CommitConfigDocsResource()
        commit_resp = None
        with patch.object(ConfigdocsHelper, 'tag_buffer') as mock_method:
            helper = ConfigdocsHelper(CTX)
            helper.is_buffer_empty = lambda: False
            helper.get_validations_for_buffer = lambda: {'status': 'Failure'}
            commit_resp = ccdr.commit_configdocs(helper, True, False)

        mock_method.assert_called_once_with('committed')
        assert '200' in commit_resp['code']
        assert 'FORCED' in commit_resp['message']
        assert commit_resp['status'] == 'Failure'

    def test_commit_configdocs_buffer_err(self):
        """
        Tests the CommitConfigDocsResource method commit_configdocs
        """
        ccdr = CommitConfigDocsResource()

        with pytest.raises(ApiError):
            helper = ConfigdocsHelper(CTX)
            helper.is_buffer_empty = lambda: True
            helper.get_validations_for_buffer = lambda: {'status': 'Success'}
            ccdr.commit_configdocs(helper, False, False)

    def test_commit_configdocs_dryrun(self):
        """
        Tests the CommitConfigDocsResource method commit_configdocs
        """
        ccdr = CommitConfigDocsResource()
        commit_resp = None
        with patch.object(ConfigdocsHelper, 'tag_buffer') as mock_method:
            helper = ConfigdocsHelper(CTX)
            helper.is_buffer_empty = lambda: False
            helper.get_validations_for_buffer = lambda: {'status': 'Success'}
            commit_resp = ccdr.commit_configdocs(helper, False, True)

        assert '200' in commit_resp['code']
        assert commit_resp['message'] == 'DRYRUN'
        assert commit_resp['status'] == 'Success'
