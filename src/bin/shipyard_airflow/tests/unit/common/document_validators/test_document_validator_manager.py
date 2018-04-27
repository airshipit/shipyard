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
"""Tests for the DocumentValidationManager"""
import mock
from mock import MagicMock

import pytest

from shipyard_airflow.common.document_validators.document_validator import (
    DocumentValidator
)
from shipyard_airflow.common.document_validators.document_validator_manager \
    import DocumentValidationManager
from shipyard_airflow.common.document_validators.errors import (
    DeckhandClientRequiredError
)


def get_doc_returner():
    placeholder = MagicMock()
    placeholder.data = {"nothing": "here"}

    def doc_returner(revision_id, rendered, **filters):
        if not revision_id == 99:
            doc = filters['metadata.name']
            if 'document-placeholder' in doc:
                return [placeholder]
        return []
    return doc_returner


def _dh_doc_client():
    dhc = MagicMock()
    dhc.revisions.documents = get_doc_returner()
    return dhc


class ValidatorA(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Error"

    def do_validate(self):
        self.error_status = True
        self.val_msg_list.append(self.val_msg(
            name="DeploymentGroupCycle",
            error=True,
            level="Error",
            message="Message Here",
            diagnostic="diags"
        ))


class ValidatorB(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Error"

    def do_validate(self):
        pass


class ValidatorB2(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Warning"

    def do_validate(self):
        pass


class ValidatorB3(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Info"

    def do_validate(self):
        pass


class ValidatorC(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Error"

    def do_validate(self):
        # all should succeed.
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-A')
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-B')
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-C')
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-D')
        self.add_triggered_validation(ValidatorC2,
                                      'document-placeholder-E')


class ValidatorC2(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Error"

    def do_validate(self):
        # all should succeed.
        self.add_triggered_validation(ValidatorC3,
                                      'document-placeholder-F')
        self.add_triggered_validation(ValidatorC3,
                                      'document-placeholder-G')
        self.add_triggered_validation(ValidatorC3,
                                      'document-placeholder-H')
        self.add_triggered_validation(ValidatorC3,
                                      'document-placeholder-I')


class ValidatorC3(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Error"

    def do_validate(self):
        # all should succeed.
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-J')
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-K')
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-L')
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-M')


class ValidatorD(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Error"

    def do_validate(self):
        # one should have errors
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-A')
        self.add_triggered_validation(ValidatorB,
                                      'document-placeholder-B')
        self.add_triggered_validation(ValidatorA,
                                      'document-placeholder-C')


class ValidatorBadMissingSeverity(DocumentValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "schema/Schema/v1"
    missing_severity = "Pancake Syrup"

    def do_validate(self):
        pass


class TestValidatorManager:
    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_simple_success(self, fake_client):
        validations = [(ValidatorB, 'document-placeholder01')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        dvm.validate()
        assert not dvm.errored
        assert dvm.validations_run == 1

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_simple_failure(self, fake_client):
        validations = [(ValidatorA, 'document-placeholder02')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        dvm.validate()
        assert dvm.errored
        assert dvm.validations_run == 1

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_chained_success(self, fake_client):
        validations = [(ValidatorC, 'document-placeholder03')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        dvm.validate()
        assert not dvm.errored
        assert dvm.validations_run == 26

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_chained_failure(self, fake_client):
        validations = [(ValidatorD, 'document-placeholder04')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        dvm.validate()
        assert dvm.errored
        assert dvm.validations_run == 4

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_missing_doc_failure_warn(self, fake_client):
        validations = [(ValidatorB2, 'missing-error')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        results = dvm.validate()
        assert dvm.errored
        assert len(results) == 1
        for r in results:
            assert r['level'] == "Warning"
            assert not r['error']

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_missing_doc_failure_info(self, fake_client):
        validations = [(ValidatorB3, 'missing-error')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        results = dvm.validate()
        assert dvm.errored
        assert len(results) == 1
        for r in results:
            assert r['level'] == "Info"
            assert not r['error']

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_missing_doc_failure(self, fake_client):
        validations = [(ValidatorB, 'missing-error')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        results = dvm.validate()
        assert dvm.errored
        assert len(results) == 1
        for r in results:
            assert r['level'] == "Error"
            assert r['error']

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=_dh_doc_client())
    def test_missing_doc_bad_severity(self, fake_client):
        validations = [(ValidatorBadMissingSeverity, 'missing-error')]
        dvm = DocumentValidationManager(fake_client(), 1, validations)
        results = dvm.validate()
        assert dvm.errored
        assert len(results) == 1
        for r in results:
            assert r['level'] == "Error"
            assert r['error']

    def test_missing_dh_client(self):
        with pytest.raises(DeckhandClientRequiredError):
            ValidatorB(deckhand_client=None, revision=1, doc_name="no")

    def test_val_msg_defaults(self):
        vb = ValidatorB(deckhand_client=MagicMock(), revision=1, doc_name="no")
        msg = vb.val_msg("hi", "nm")
        assert msg['error']
        assert msg['level'] == "Error"
        assert msg['diagnostic'] == "Message generated by Shipyard."
        assert msg['documents'] == [{"name": "no",
                                     "schema": "schema/Schema/v1"}]
