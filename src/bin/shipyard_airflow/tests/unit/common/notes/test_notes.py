# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
"""Tests for the Notes component"""
from unittest import mock

import pytest
import responses

from shipyard_airflow.common.notes.errors import (
    NotesInitializationError,
    NotesRetrievalError,
    NotesStorageError
)
from shipyard_airflow.common.notes.notes import (
    Note,
    NotesManager,
    NotesStorage,
    Query
)
from shipyard_airflow.common.notes.storage_impl_mem import MemoryNotesStorage


def get_token():
    return "token"


class NotesStorageErrorImpl(NotesStorage):
    def store(self, note):
        raise Exception("Didn't see it coming")

    def retrieve(self, query):
        raise Exception("Outta Nowhere")


class NotesStorageExpectedErrorImpl(NotesStorage):
    def store(self, note):
        raise NotesStorageError("Expected")

    def retrieve(self, query):
        raise NotesRetrievalError("Expected")


class TestNotesManager:
    def test_init(self):
        with pytest.raises(NotesInitializationError) as nie:
            nm = NotesManager(None, None)
        assert "Storage object is not" in str(nie.value)

        with pytest.raises(NotesInitializationError) as nie:
            nm = NotesManager({}, None)
        assert "Storage object is not" in str(nie.value)

        with pytest.raises(NotesInitializationError) as nie:
            nm = NotesManager(MemoryNotesStorage(), None)
        assert "Parameter get_token" in str(nie.value)

        with pytest.raises(NotesInitializationError) as nie:
            nm = NotesManager(MemoryNotesStorage(), {})
        assert "Parameter get_token" in str(nie.value)

        nm = NotesManager(MemoryNotesStorage(), get_token)
        assert nm.connect_timeout == 3
        assert nm.read_timeout == 10

        nm = NotesManager(MemoryNotesStorage(), get_token, connect_timeout=99,
                          read_timeout=999)
        assert nm.connect_timeout == 99
        assert nm.read_timeout == 999
        assert isinstance(nm.storage, MemoryNotesStorage)

    def test_store_retrieve_expected_exception_handling(self):
        nm = NotesManager(NotesStorageExpectedErrorImpl(), get_token)
        with pytest.raises(NotesStorageError) as nse:
            n = Note(
                assoc_id="test1/11111/aaa",
                subject="store_retrieve_1",
                sub_type="test",
                note_val="this is my note 1"
            )
            n.note_id = None
            nm.store(n)
        assert "Expected" == str(nse.value)

        with pytest.raises(NotesRetrievalError) as nse:
            nm.retrieve(Query("test"))
        assert "Expected" == str(nse.value)

    def test_store_retrieve_unexpected_exception_handling(self):
        nm = NotesManager(NotesStorageErrorImpl(), get_token)
        with pytest.raises(NotesStorageError) as nse:
            n = Note(
                assoc_id="test1/11111/aaa",
                subject="store_retrieve_1",
                sub_type="test",
                note_val="this is my note 1"
            )
            n.note_id = None
            nm.store(n)
        assert "Unhandled" in str(nse.value)

        with pytest.raises(NotesRetrievalError) as nse:
            nm.retrieve(Query("test"))
        assert "Unhandled" in str(nse.value)

    def test_store_retrieve_basic(self):
        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/aaa",
            subject="store_retrieve_1",
            sub_type="test",
            note_val="this is my note 1"
        ))
        n_list = nm.retrieve(Query("test1"))
        assert len(n_list) == 1
        assert n_list[0].subject == "store_retrieve_1"
        n_list = nm.retrieve(Query("test2"))
        assert len(n_list) == 0

    def test_store_retrieve_basic_verbosity(self):
        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/aaa",
            subject="store_retrieve_1",
            sub_type="test",
            note_val="this is my note 1",
            verbosity=5
        ))
        n_list = nm.retrieve(Query("test1", max_verbosity=3))
        assert len(n_list) == 0

    def test_store_bad_verbosity(self):
        nm = NotesManager(MemoryNotesStorage(), get_token)
        with pytest.raises(NotesStorageError) as nse:
            nm.store(Note(
                assoc_id="test1/11111/aaa",
                subject="store_retrieve_1",
                sub_type="test",
                note_val="this is my note 1",
                verbosity=-4
            ))
        assert "Verbosity of notes must" in str(nse.value)

        with pytest.raises(NotesStorageError) as nse:
            nm.store(Note(
                assoc_id="test1/11111/aaa",
                subject="store_retrieve_1",
                sub_type="test",
                note_val="this is my note 1",
                verbosity=6
            ))
        assert "Verbosity of notes must" in str(nse.value)

    def test_store_retrieve_multi(self):
        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/aaa",
            subject="store_retrieve",
            sub_type="test",
            note_val="this is my note 1"
        ))
        nm.store(Note(
            assoc_id="test1/11111/bbb",
            subject="store_retrieve",
            sub_type="test",
            note_val="this is my note 2"
        ))
        nm.store(Note(
            assoc_id="test2/2222/aaa",
            subject="store_retrieve_2",
            sub_type="test",
            note_val="this is my note 3"
        ))
        n_list = nm.retrieve(Query("test2"))
        assert len(n_list) == 1
        assert n_list[0].subject == "store_retrieve_2"
        n_list = nm.retrieve(Query("test1"))
        assert len(n_list) == 2
        n_list = nm.retrieve(Query("test1", exact_match=True))
        assert len(n_list) == 0
        n_list = nm.retrieve(Query("test1/11111/aaa", exact_match=True))
        assert len(n_list) == 1

    @responses.activate
    def test_store_retrieve_urls(self):
        responses.add(
            method="GET",
            url="http://test.test",
            body="Hello from testland",
            status=200,
            content_type="text/plain"
        )
        responses.add(
            method="GET",
            url="http://test.test2",
            body="Hello from testland2",
            status=200,
            content_type="text/plain"
        )

        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/aaa",
            subject="store_retrieve3",
            sub_type="test",
            note_val="this is my note 1",
            link_url="http://test.test/"
        ))
        nm.store(Note(
            assoc_id="test1/11111/bbb",
            subject="store_retrieve3",
            sub_type="test",
            note_val="this is my note 2",
            link_url="http://test.test2/"
        ))
        n_list = nm.retrieve(Query("test1"))
        assert len(n_list) == 2
        for n in n_list:
            assert n.resolved_url_value.startswith("Hello from testland")
        with pytest.raises(KeyError):
            auth_hdr = responses.calls[0].request.headers['X-Auth-Token']

    @responses.activate
    def test_store_retrieve_url_bad_status_code(self):
        responses.add(
            method="GET",
            url="http://test.test",
            body="What note?",
            status=404,
            content_type="text/plain"
        )
        responses.add(
            method="GET",
            url="http://test.test2",
            body="Hello from testland2",
            status=200,
            content_type="text/plain"
        )

        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/aaa",
            subject="store_retrieve3",
            sub_type="test",
            note_val="this is my note 1",
            link_url="http://test.test/"
        ))
        nm.store(Note(
            assoc_id="test1/11111/bbb",
            subject="store_retrieve3",
            sub_type="test",
            note_val="this is my note 2",
            link_url="http://test.test2/"
        ))
        n_list = nm.retrieve(Query("test1"))
        assert len(n_list) == 2
        for n in n_list:
            if n.assoc_id == "test1/11111/aaa":
                assert "failed with status code: 404" in n.resolved_url_value
            else:
                assert n.resolved_url_value.startswith("Hello from testland")

    @responses.activate
    def test_store_retrieve_url_does_not_exist(self):
        responses.add(
            method="GET",
            url="http://test.test2",
            body="Hello from testland2",
            status=200,
            content_type="text/plain"
        )

        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/aaa",
            subject="store_retrieve3",
            sub_type="test",
            note_val="this is my note 1",
            link_url="test_breakage://test.test/"
        ))
        nm.store(Note(
            assoc_id="test1/11111/bbb",
            subject="store_retrieve3",
            sub_type="test",
            note_val="this is my note 2",
            link_url="http://test.test2/"
        ))
        n_list = nm.retrieve(Query("test1"))
        assert len(n_list) == 2
        for n in n_list:
            if n.assoc_id == "test1/11111/aaa":
                assert "URL lookup was unable" in n.resolved_url_value
            else:
                assert n.resolved_url_value.startswith("Hello from testland")

    @responses.activate
    def test_store_retrieve_with_auth(self):
        responses.add(
            method="GET",
            url="http://test.test2",
            body="Hello from testland2",
            status=200,
            content_type="text/plain"
        )

        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/bbb",
            subject="store_retrieve3",
            sub_type="test",
            note_val="this is my note 2",
            link_url="http://test.test2/",
            is_auth_link=True
        ))
        n_list = nm.retrieve(Query("test1"))
        assert len(n_list) == 1
        for n in n_list:
            assert n.resolved_url_value == "Hello from testland2"
        auth_hdr = responses.calls[0].request.headers['X-Auth-Token']
        assert 'token' == auth_hdr

    def test_note_view(self):
        nm = NotesManager(MemoryNotesStorage(), get_token)
        nm.store(Note(
            assoc_id="test1/11111/aaa",
            subject="store_retrieve_1",
            sub_type="test",
            note_val="this is my note 1"
        ))
        n_list = nm.retrieve(Query("test1"))
        assert len(n_list) == 1
        nid = n_list[0].note_id
        nt = n_list[0].note_timestamp
        assert n_list[0].view() == {
            'assoc_id': 'test1/11111/aaa',
            'subject': 'store_retrieve_1',
            'sub_type': 'test',
            'note_val': 'this is my note 1',
            'verbosity': 1,
            'note_id': nid,
            'note_timestamp': nt,
            'resolved_url_value': None,
        }
