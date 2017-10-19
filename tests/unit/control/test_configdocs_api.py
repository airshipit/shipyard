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
""" Tests for the configdocs_api
"""
from mock import patch

import pytest

from shipyard_airflow.control.configdocs.configdocs_api import (
    CommitConfigDocsResource,
    ConfigDocsResource
)
from shipyard_airflow.control.configdocs.configdocs_helper import \
    ConfigdocsHelper
from shipyard_airflow.errors import ApiError


def test__validate_version_parameter():
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


def test_get_collection():
    helper = None
    with patch.object(ConfigdocsHelper, 'get_collection_docs') as mock_method:
        cdr = ConfigDocsResource()
        helper = ConfigdocsHelper('')
        cdr.get_collection(helper, 'apples')

    mock_method.assert_called_once_with('buffer', 'apples')


def test_post_collection():
    """
    Tests the post collection method of the ConfigdocsResource
    """
    helper = None
    collection_id = 'trees'
    document_data = 'lots of info'
    with patch.object(ConfigdocsHelper, 'add_collection') as mock_method:
        cdr = ConfigDocsResource()
        helper = ConfigdocsHelper('')
        helper.is_buffer_valid_for_bucket = lambda a, b: True
        helper.get_deckhand_validation_status = (
            lambda a: ConfigdocsHelper._format_validations_to_status([], 0)
        )
        cdr.post_collection(helper=helper,
                            collection_id=collection_id,
                            document_data=document_data)

    mock_method.assert_called_once_with(collection_id, document_data)

    with pytest.raises(ApiError):
        cdr = ConfigDocsResource()
        helper = ConfigdocsHelper('')
        # not valid for bucket
        helper.is_buffer_valid_for_bucket = lambda a, b: False
        helper.get_deckhand_validation_status = (
            lambda a: ConfigdocsHelper._format_validations_to_status([], 0)
        )
        cdr.post_collection(helper=helper,
                            collection_id=collection_id,
                            document_data=document_data)


def test_commit_configdocs():
    """
    Tests the CommitConfigDocsResource method commit_configdocs
    """
    ccdr = CommitConfigDocsResource()
    commit_resp = None
    with patch.object(ConfigdocsHelper, 'tag_buffer') as mock_method:
        helper = ConfigdocsHelper('')
        helper.is_buffer_empty = lambda: False
        helper.get_validations_for_buffer = lambda: {'status': 'Valid'}
        commit_resp = ccdr.commit_configdocs(helper, False)

    mock_method.assert_called_once_with('committed')
    assert commit_resp['status'] == 'Valid'

    commit_resp = None
    with patch.object(ConfigdocsHelper, 'tag_buffer') as mock_method:
        helper = ConfigdocsHelper('')
        helper.is_buffer_empty = lambda: False
        helper.get_validations_for_buffer = (
            lambda: {
                'status': 'Invalid',
                'code': '400 Bad Request',
                'message': 'this is a mock response'
            }
        )
        commit_resp = ccdr.commit_configdocs(helper, False)
    assert '400' in commit_resp['code']
    assert commit_resp['message'] is not None
    assert commit_resp['status'] == 'Invalid'


def test_commit_configdocs_force():
    """
    Tests the CommitConfigDocsResource method commit_configdocs
    """
    ccdr = CommitConfigDocsResource()
    commit_resp = None
    with patch.object(ConfigdocsHelper, 'tag_buffer') as mock_method:
        helper = ConfigdocsHelper('')
        helper.is_buffer_empty = lambda: False
        helper.get_validations_for_buffer = lambda: {'status': 'Invalid'}
        commit_resp = ccdr.commit_configdocs(helper, True)

    mock_method.assert_called_once_with('committed')
    print(commit_resp)
    assert '200' in commit_resp['code']
    assert 'FORCED' in commit_resp['message']
    assert commit_resp['status'] == 'Invalid'


def test_commit_configdocs_buffer_err():
    """
    Tests the CommitConfigDocsResource method commit_configdocs
    """
    ccdr = CommitConfigDocsResource()

    with pytest.raises(ApiError):
        helper = ConfigdocsHelper('')
        helper.is_buffer_empty = lambda: True
        helper.get_validations_for_buffer = lambda: {'status': 'Valid'}
        ccdr.commit_configdocs(helper, False)
