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
"""Tests for the action validators run when an action is created"""
import mock
from mock import MagicMock
import yaml

import pytest

from shipyard_airflow.control.action.action_validators import (
    validate_site_action
)
from shipyard_airflow.errors import ApiError
from tests.unit.common.deployment_group.node_lookup_stubs import node_lookup
import tests.unit.common.deployment_group.test_deployment_group_manager as tdgm


def get_doc_returner(style, ds_name):
    strategy = MagicMock()
    if style == 'cycle':
        strategy.data = {"groups": yaml.safe_load(tdgm._CYCLE_GROUPS_YAML)}
    elif style == 'clean':
        strategy.data = {"groups": yaml.safe_load(tdgm._GROUPS_YAML)}

    def doc_returner(revision_id, rendered, **filters):
        if not revision_id == 99:
            doc = filters['metadata.name']
            if doc == 'deployment-configuration':
                dc = MagicMock()
                dc.data = {
                    "physical_provisioner": {
                        "deployment_strategy": ds_name
                    },
                    "armada": {
                        "manifest": "full-site"
                    }
                }
                # if passed a name of 'defaulted' clear the section
                if ds_name == 'defaulted':
                    dc.data["physical_provisioner"] = None
                print(dc.__dict__)
                return [dc]
            elif doc == 'dep-strat':
                return [strategy]
        return []
    return doc_returner


def fake_dh_doc_client(style, ds_name='dep-strat'):
    dhc = MagicMock()
    dhc.revisions.documents = get_doc_returner(style, ds_name)
    return dhc


class TestActionValidator:

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_site_action(self, *args):
        """Test the function that runs the validator class"""
        try:
            validate_site_action({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        except Exception as ex:
            # any exception is a failure
            assert False, str(ex)

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('cycle'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_site_action_cycle(self, *args):
        """Test the function that runs the validator class with a
        deployment strategy that has a cycle in the groups
        """
        with pytest.raises(ApiError) as apie:
            validate_site_action({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        assert apie.value.description == 'InvalidConfigurationDocuments'
        assert (
            'The following are involved in a circular dependency:'
        ) in apie.value.error_list[0]['diagnostic']

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean', ds_name='not-there'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_site_action_missing_dep_strat(self, *args):
        """Test the function that runs the validator class with a missing
        deployment strategy - specified, but not present
        """
        with pytest.raises(ApiError) as apie:
            validate_site_action({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        assert apie.value.description == 'InvalidConfigurationDocuments'
        assert apie.value.error_list[0]['name'] == 'DocumentNotFoundError'

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean'), ds_name='defaulted')
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_site_action_default_dep_strat(self, *args):
        """Test the function that runs the validator class with a defaulted
        deployment strategy (not specified)
        """
        try:
            validate_site_action({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        except:
            # any exception is a failure
            assert False

    def test_validate_site_missing_rev(self):
        """Test the function that runs the validator class with a
        deployment strategy that has a cycle in the groups
        """
        with pytest.raises(ApiError) as apie:
            validate_site_action({
                'id': '123',
                'name': 'deploy_site'
            })
        assert apie.value.description == 'InvalidDocumentRevision'

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean', ds_name='not-there'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_site_action_continue_failure(self, *args):
        """Test the function that runs the validator class with a defaulted
        deployment strategy (not specified)
        """
        try:
            validate_site_action({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1,
                'parameters': {'continue-on-fail': 'true'}
            })
        except:
            # any exception is a failure
            assert False
