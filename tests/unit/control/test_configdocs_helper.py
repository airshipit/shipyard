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
import json
from unittest.mock import patch
import yaml

import pytest

from .fake_response import FakeResponse
from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.control.configdocs import configdocs_helper
from shipyard_airflow.control.configdocs.configdocs_helper import (
    BufferMode,
    ConfigdocsHelper
)
from shipyard_airflow.control.configdocs.deckhand_client import (
    DeckhandClient,
    DeckhandPaths,
    DeckhandResponseError,
    NoRevisionsExistError
)
from shipyard_airflow.errors import ApiError, AppError

CTX = ShipyardRequestContext()

REV_BUFFER_DICT = {
    'committed': {'id': 3,
                  'url': 'url3',
                  'createdAt': '2017-07-14T21:23Z',
                  'buckets': ['mop', 'slop'],
                  'tags': ['committed'],
                  'validationPolicies': {}},
    'buffer': {'id': 5,
               'url': 'url5',
               'createdAt': '2017-07-16T21:23Z',
               'buckets': ['mop', 'chum'],
               'tags': ['deckhand_sez_hi'],
               'validationPolicies': {}},
    'latest': {'id': 5,
               'url': 'url5',
               'createdAt': '2017-07-16T21:23Z',
               'buckets': ['mop', 'chum'],
               'tags': ['deckhand_sez_hi'],
               'validationPolicies': {}},
    'revision_count': 5
}

DIFF_BUFFER_DICT = {
    'mop': 'unmodified',
    'chum': 'created',
    'slop': 'deleted'
}

REV_BUFF_EMPTY_DICT = {
    'committed': {'id': 3,
                  'url': 'url3',
                  'createdAt': '2017-07-14T21:23Z',
                  'buckets': ['mop'],
                  'tags': ['committed'],
                  'validationPolicies': {}},
    'buffer': None,
    'latest': {'id': 3,
               'url': 'url3',
               'createdAt': '2017-07-14T21:23Z',
               'buckets': ['mop'],
               'tags': ['committed'],
               'validationPolicies': {}},
    'revision_count': 3
}

DIFF_BUFF_EMPTY_DICT = {
    'mop': 'unmodified'
}

REV_NO_COMMIT_DICT = {
    'committed': None,
    'buffer': {'id': 3,
               'url': 'url3',
               'createdAt': '2017-07-14T21:23Z',
               'buckets': ['mop'],
               'tags': [],
               'validationPolicies': {}},
    'latest': {'id': 3,
               'url': 'url3',
               'createdAt': '2017-07-14T21:23Z',
               'buckets': ['mop'],
               'tags': [],
               'validationPolicies': {}},
    'revision_count': 3
}

DIFF_NO_COMMIT_DICT = {
    'mop': 'created'
}

REV_EMPTY_DICT = {
    'committed': None,
    'buffer': None,
    'latest': None,
    'revision_count': 0
}

DIFF_EMPTY_DICT = {}

REV_COMMIT_AND_BUFFER_DICT = {
    'committed': {'id': 1,
                  'url': 'url3',
                  'createdAt': '2017-07-14T21:23Z',
                  'buckets': ['mop'],
                  'tags': ['committed'],
                  'validationPolicies': {}},
    'buffer': {'id': 3,
               'url': 'url3',
               'createdAt': '2017-07-14T21:23Z',
               'buckets': ['mop'],
               'tags': [],
               'validationPolicies': {}},
    'latest': {'id': 3,
               'url': 'url3',
               'createdAt': '2017-07-14T21:23Z',
               'buckets': ['mop'],
               'tags': [],
               'validationPolicies': {}},
    'revision_count': 3
}

DIFF_COMMIT_AND_BUFFER_DICT = {
    'mop': 'modified'
}


def test_construct_configdocs_helper():
    """
    Creates a configdoc helper, tests that the context
    is passed to the sub-helper
    """
    helper = ConfigdocsHelper(CTX)
    assert helper.ctx == CTX


def test_get_buffer_mode():
    """
    ensures that strings passed to get_buffer_mode are properly handled
    """
    # None cases
    assert ConfigdocsHelper.get_buffer_mode(
        ''
    ) == BufferMode.REJECTONCONTENTS
    assert ConfigdocsHelper.get_buffer_mode(
        None
    ) == BufferMode.REJECTONCONTENTS

    # valid cases
    assert ConfigdocsHelper.get_buffer_mode(
        'rejectoncontents'
    ) == BufferMode.REJECTONCONTENTS
    assert ConfigdocsHelper.get_buffer_mode(
        'append'
    ) == BufferMode.APPEND
    assert ConfigdocsHelper.get_buffer_mode(
        'replace'
    ) == BufferMode.REPLACE

    # case insensitive
    assert ConfigdocsHelper.get_buffer_mode(
        'ReJEcTOnConTenTs'
    ) == BufferMode.REJECTONCONTENTS

    # bad value
    assert ConfigdocsHelper.get_buffer_mode(
        'hippopotomus'
    ) is None


def test_is_buffer_emtpy():
    """
    Test the method to check if the configdocs buffer is empty
    """
    helper = ConfigdocsHelper(CTX)
    helper._get_revision_dict = lambda: REV_BUFFER_DICT
    assert not helper.is_buffer_empty()

    helper._get_revision_dict = lambda: REV_BUFF_EMPTY_DICT
    assert helper.is_buffer_empty()

    helper._get_revision_dict = lambda: REV_NO_COMMIT_DICT
    assert not helper.is_buffer_empty()

    helper._get_revision_dict = lambda: REV_EMPTY_DICT
    assert helper.is_buffer_empty()


def test_is_collection_in_buffer():
    """
    Test that collections are found in the buffer
    """
    helper = ConfigdocsHelper(CTX)
    helper._get_revision_dict = lambda: REV_BUFFER_DICT
    helper.deckhand.get_diff = (
        lambda old_revision_id, new_revision_id: DIFF_BUFFER_DICT
    )
    # mop is not in buffer; chum and slop are in buffer.
    # unmodified means it is not in buffer
    assert not helper.is_collection_in_buffer('mop')
    # created means it is in buffer
    assert helper.is_collection_in_buffer('slop')
    # deleted means it is in buffer
    assert helper.is_collection_in_buffer('chum')

    def _raise_dre():
        raise DeckhandResponseError(
            status_code=9000,
            response_message='This is bogus'
        )

    helper._get_revision_dict = _raise_dre

    with pytest.raises(DeckhandResponseError):
        helper.is_collection_in_buffer('does not matter')


def test_is_buffer_valid_for_bucket():
    """
    def is_buffer_valid_for_bucket(self, collection_id, buffermode)
    """

    def set_revision_dict(helper, revision_dict, diff_dict):
        helper._get_revision_dict = lambda: revision_dict
        helper.deckhand.get_diff = lambda: diff_dict

    helper = ConfigdocsHelper(CTX)
    helper._get_revision_dict = lambda: REV_BUFFER_DICT
    helper.deckhand.get_diff = (
        lambda old_revision_id, new_revision_id: DIFF_BUFFER_DICT
    )
    helper.deckhand.rollback = lambda target_revision_id: (
        set_revision_dict(helper, REV_BUFF_EMPTY_DICT, DIFF_BUFF_EMPTY_DICT)
    )
    # patch the deckhand client method to set to empty if reset_to_empty
    # is invoked.
    helper.deckhand.reset_to_empty = lambda: (
        set_revision_dict(helper, REV_EMPTY_DICT, DIFF_EMPTY_DICT)
    )

    # can add 'mop' on append, it was unmodified in buffer
    # can add 'water' on append, it was not anywhere before
    # can't add 'slop' on append, it was deleted (modified in buffer)
    # can't add 'chum' on append, it is already in buffer
    # can't add anything on rejectoncontents
    # can add anything on replace
    assert helper.is_buffer_valid_for_bucket('mop', BufferMode.APPEND)
    assert helper.is_buffer_valid_for_bucket('water', BufferMode.APPEND)
    assert not helper.is_buffer_valid_for_bucket('slop', BufferMode.APPEND)
    assert not helper.is_buffer_valid_for_bucket('chum', BufferMode.APPEND)
    assert not helper.is_buffer_valid_for_bucket('new',
                                                 BufferMode.REJECTONCONTENTS)

    # because of the patched methods above, replace mode will set the
    # buffer/diff to values as if it were rolled back.
    assert helper.is_buffer_valid_for_bucket('mop', BufferMode.REPLACE)
    # should be able to replace mode even if no buffer contents.
    assert helper.is_buffer_valid_for_bucket('mop', BufferMode.REPLACE)
    # in rolled back state as per last two commands, should be ok
    # to use rejectoncontents to add.
    assert helper.is_buffer_valid_for_bucket('mop',
                                             BufferMode.REJECTONCONTENTS)

    # set up as if there is no committed revision yet
    helper._get_revision_dict = lambda: REV_NO_COMMIT_DICT
    helper.deckhand.get_diff = (
        lambda old_revision_id, new_revision_id: DIFF_NO_COMMIT_DICT
    )

    assert helper.is_buffer_valid_for_bucket('slop', BufferMode.APPEND)
    assert helper.is_buffer_valid_for_bucket('chum', BufferMode.APPEND)
    # buffer is not empty, reject on contents.
    assert not helper.is_buffer_valid_for_bucket('new',
                                                 BufferMode.REJECTONCONTENTS)

    # This should rollback to "nothing" using reset to empty.
    assert helper.is_buffer_valid_for_bucket('mop', BufferMode.REPLACE)
    assert helper.is_buffer_empty()

    # set up as if there is nothing in deckhand.
    helper._get_revision_dict = lambda: REV_EMPTY_DICT
    helper.deckhand.get_diff = (
        lambda old_revision_id, new_revision_id: DIFF_EMPTY_DICT
    )
    # should be able to add in any mode.
    assert helper.is_buffer_valid_for_bucket('slop', BufferMode.APPEND)
    assert helper.is_buffer_valid_for_bucket('chum', BufferMode.APPEND)
    assert helper.is_buffer_valid_for_bucket('new',
                                             BufferMode.REJECTONCONTENTS)
    assert helper.is_buffer_valid_for_bucket('mop', BufferMode.REPLACE)


def test__get_revision_dict_no_commit():
    """
    Tests the processing of revision dict response from dechand
    with a buffer version, but no committed revision
    """
    helper = ConfigdocsHelper(CTX)
    helper.deckhand.get_revision_list = lambda: yaml.load("""
---
  - id: 1
    url: https://deckhand/api/v1.0/revisions/1
    createdAt: 2017-07-14T21:23Z
    buckets: [mop]
    tags: [a, b, c]
    validationPolicies:
      site-deploy-validation:
        status: failed
  - id: 2
    url: https://deckhand/api/v1.0/revisions/2
    createdAt: 2017-07-16T01:15Z
    buckets: [flop, mop]
    tags: [b]
    validationPolicies:
      site-deploy-validation:
        status: succeeded
...
""")
    rev_dict = helper._get_revision_dict()
    committed = rev_dict.get(configdocs_helper.COMMITTED)
    buffer = rev_dict.get(configdocs_helper.BUFFER)
    latest = rev_dict.get(configdocs_helper.LATEST)
    count = rev_dict.get(configdocs_helper.REVISION_COUNT)
    assert committed is None
    assert buffer.get('id') == 2
    assert latest.get('id') == 2
    assert count == 2


def test__get_revision_dict_empty():
    """
    Tests the processing of revision dict response from dechand
    where the response is an empty list
    """
    helper = ConfigdocsHelper(CTX)
    helper.deckhand.get_revision_list = lambda: []
    rev_dict = helper._get_revision_dict()
    committed = rev_dict.get(configdocs_helper.COMMITTED)
    buffer = rev_dict.get(configdocs_helper.BUFFER)
    latest = rev_dict.get(configdocs_helper.LATEST)
    count = rev_dict.get(configdocs_helper.REVISION_COUNT)
    assert committed is None
    assert buffer is None
    assert latest is None
    assert count == 0


def test__get_revision_dict_commit_no_buff():
    """
    Tests the processing of revision dict response from dechand
    with a committed and no buffer revision
    """
    helper = ConfigdocsHelper(CTX)
    helper.deckhand.get_revision_list = lambda: yaml.load("""
---
  - id: 1
    url: https://deckhand/api/v1.0/revisions/1
    createdAt: 2017-07-14T21:23Z
    buckets: [mop]
    tags: [a, b, c]
    validationPolicies:
      site-deploy-validation:
        status: failed
  - id: 2
    url: https://deckhand/api/v1.0/revisions/2
    createdAt: 2017-07-16T01:15Z
    buckets: [flop, mop]
    tags: [b, committed]
    validationPolicies:
      site-deploy-validation:
        status: succeeded
...
""")
    rev_dict = helper._get_revision_dict()
    committed = rev_dict.get(configdocs_helper.COMMITTED)
    buffer = rev_dict.get(configdocs_helper.BUFFER)
    latest = rev_dict.get(configdocs_helper.LATEST)
    count = rev_dict.get(configdocs_helper.REVISION_COUNT)
    assert committed.get('id') == 2
    assert buffer is None
    assert latest.get('id') == 2
    assert count == 2


def test__get_revision_dict_commit_and_buff():
    """
    Tests the processing of revision dict response from dechand
    with a committed and a buffer revision
    """
    helper = ConfigdocsHelper(CTX)
    helper.deckhand.get_revision_list = lambda: yaml.load("""
---
  - id: 1
    url: https://deckhand/api/v1.0/revisions/1
    createdAt: 2017-07-14T21:23Z
    buckets: [mop]
    tags: [a, b, committed]
    validationPolicies:
      site-deploy-validation:
        status: failed
  - id: 2
    url: https://deckhand/api/v1.0/revisions/2
    createdAt: 2017-07-16T01:15Z
    buckets: [flop, mop]
    tags: [b]
    validationPolicies:
      site-deploy-validation:
        status: succeeded
...
""")
    rev_dict = helper._get_revision_dict()
    committed = rev_dict.get(configdocs_helper.COMMITTED)
    buffer = rev_dict.get(configdocs_helper.BUFFER)
    latest = rev_dict.get(configdocs_helper.LATEST)
    count = rev_dict.get(configdocs_helper.REVISION_COUNT)
    assert committed.get('id') == 1
    assert buffer.get('id') == 2
    assert latest.get('id') == 2
    assert count == 2


def test__get_revision_dict_errs():
    """
    tests getting a revision dictionary method when the deckhand
    client has raised an exception
    """
    def _raise_dre():
        raise DeckhandResponseError(
            status_code=9000,
            response_message='This is bogus'
        )

    def _raise_nree():
        raise NoRevisionsExistError()

    helper = ConfigdocsHelper(CTX)
    helper.deckhand.get_revision_list = _raise_dre

    with pytest.raises(AppError):
        helper._get_revision_dict()

    helper.deckhand.get_revision_list = _raise_nree
    rev_dict = helper._get_revision_dict()
    committed = rev_dict.get(configdocs_helper.COMMITTED)
    buffer = rev_dict.get(configdocs_helper.BUFFER)
    latest = rev_dict.get(configdocs_helper.LATEST)
    count = rev_dict.get(configdocs_helper.REVISION_COUNT)
    assert committed is None
    assert buffer is None
    assert latest is None
    assert count == 0


def test_get_collection_docs():
    """
    Returns the representation of the yaml docs from deckhand
    """
    helper = ConfigdocsHelper(CTX)
    helper.deckhand.get_docs_from_revision = (
        lambda revision_id, bucket_id: "{'yaml': 'yaml'}"
    )
    helper._get_revision_dict = lambda: REV_EMPTY_DICT
    helper.deckhand.get_diff = (
        lambda old_revision_id, new_revision_id: DIFF_EMPTY_DICT
    )

    with pytest.raises(ApiError):
        helper.get_collection_docs(configdocs_helper.BUFFER, 'mop')

    with pytest.raises(ApiError):
        helper.get_collection_docs(configdocs_helper.COMMITTED, 'mop')

    helper._get_revision_dict = lambda: REV_COMMIT_AND_BUFFER_DICT
    helper.deckhand.get_diff = (
        lambda old_revision_id, new_revision_id: DIFF_COMMIT_AND_BUFFER_DICT
    )
    yaml_str = helper.get_collection_docs(configdocs_helper.BUFFER, 'mop')
    print(yaml_str)
    assert len(yaml_str) == 16

    yaml_str = helper.get_collection_docs(configdocs_helper.COMMITTED, 'mop')
    print(yaml_str)
    assert len(yaml_str) == 16


def _fake_get_validation_endpoints():
    val_ep = '{}/validatedesign'
    return [
        {'name': 'Drydock', 'url': val_ep.format('drydock')},
        {'name': 'Armada', 'url': val_ep.format('armada')},
    ]


def _fake_get_validations_for_component(url,
                                        design_reference,
                                        response,
                                        exception,
                                        context_marker,
                                        **kwargs):
    """
    Responds with a status response
    """
    response['response'] = json.loads(("""
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Failure",
  "message": "%s",
  "reason": "appropriate reason phrase",
  "details": {
    "errorCount": 2,
    "messageList": [
       { "message" : "broke it 1", "error": true},
       { "message" : "speeling error", "error": true}
    ]
  },
  "code": 400
}

""") % url)


def test_get_validations_for_revision():
    """
    Tets the functionality of the get_validations_for_revision method
    """
    with patch('shipyard_airflow.control.configdocs.deckhand_client.'
               'DeckhandClient.get_path') as mock_get_path:
        mock_get_path.return_value = 'path{}'
        helper = ConfigdocsHelper(CTX)
        hold_ve = helper.__class__._get_validation_endpoints
        hold_vfc = helper.__class__._get_validations_for_component
        helper.__class__._get_validation_endpoints = (
            _fake_get_validation_endpoints
        )
        helper.__class__._get_validations_for_component = (
            _fake_get_validations_for_component
        )
        helper._get_deckhand_validations = lambda revision_id: []
        try:
            val_status = helper.get_validations_for_revision(3)
            err_count = val_status['details']['errorCount']
            err_list_count = len(val_status['details']['messageList'])
            assert err_count == err_list_count
            assert val_status['details']['errorCount'] == 4
        finally:
            helper.__class__._get_validation_endpoints = hold_ve
            helper.__class__._get_validations_for_component = hold_vfc
    mock_get_path.assert_called_with(DeckhandPaths.RENDERED_REVISION_DOCS)


FK_VAL_BASE_RESP = FakeResponse(status_code=200, text="""
---
count: 2
next: null
prev: null
results:
  - name: deckhand-schema-validation
    url: https://deckhand/a/url/too/long/for/pep8
    status: success
  - name: promenade-site-validation
    url: https://deckhand/a/url/too/long/for/pep8
    status: failure
...
""")

FK_VAL_SUBSET_RESP = FakeResponse(status_code=200, text="""
---
count: 1
next: null
prev: null
results:
  - id: 0
    url: https://deckhand/a/url/too/long/for/pep8
    status: failure
...
""")


FK_VAL_ENTRY_RESP = FakeResponse(status_code=200, text="""
---
name: promenade-site-validation
url: https://deckhand/a/url/too/long/for/pep8
status: failure
createdAt: 2017-07-16T02:03Z
expiresAfter: null
expiresAt: null
errors:
  - documents:
      - schema: promenade/Node/v1
        name: node-document-name
      - schema: promenade/Masters/v1
        name: kubernetes-masters
    message: Node has master role, but not included in cluster masters list.
...
""")


def test__get_deckhand_validations():
    """
    Tets the functionality of processing a response from deckhand
    """
    helper = ConfigdocsHelper(CTX)
    helper.deckhand._get_base_validation_resp = (
        lambda revision_id: FK_VAL_BASE_RESP
    )
    helper.deckhand._get_subset_validation_response = (
        lambda reivsion_id, subset_name: FK_VAL_SUBSET_RESP
    )
    helper.deckhand._get_entry_validation_response = (
        lambda reivsion_id, subset_name, entry_id: FK_VAL_ENTRY_RESP
    )
    assert len(helper._get_deckhand_validations(5)) == 2


def test_tag_buffer():
    """
    Tests that the tag buffer method attempts to tag the right version
    """
    with patch.object(ConfigdocsHelper, 'tag_revision') as mock_method:
        helper = ConfigdocsHelper(CTX)
        helper._get_revision_dict = lambda: REV_BUFFER_DICT
        helper.tag_buffer('artful')

    mock_method.assert_called_once_with(5, 'artful')


def test_add_collection():
    """
    Tests the adding of a collection to deckhand - primarily
    error handling
    """
    with patch.object(DeckhandClient, 'put_bucket') as mock_method:
        helper = ConfigdocsHelper(CTX)
        helper._get_revision_dict = lambda: REV_BUFFER_DICT
        assert helper.add_collection('mop', 'yaml:yaml') == 5

    mock_method.assert_called_once_with('mop', 'yaml:yaml')
