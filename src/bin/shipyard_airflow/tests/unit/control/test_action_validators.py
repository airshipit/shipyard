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
from unittest import mock
from unittest.mock import MagicMock

import pytest
import yaml

from shipyard_airflow.common.deployment_group.errors import (
    DeploymentGroupCycleError,
    InvalidDeploymentGroupError,
    InvalidDeploymentGroupNodeLookupError
)
from shipyard_airflow.control.action.action_validators import (
    validate_committed_revision,
    validate_deployment_action_basic,
    validate_deployment_action_full,
    validate_intermediate_commits,
    validate_target_nodes
)
from shipyard_airflow.errors import ApiError
from tests.unit.common.deployment_group.node_lookup_stubs import node_lookup
import tests.unit.common.deployment_group.test_deployment_group_manager as tdgm


def get_doc_returner(style, ds_name):
    strategy = MagicMock()
    if style == 'cycle':
        strategy.data = {"groups": yaml.safe_load(tdgm.CYCLE_GROUPS_YAML)}
    elif style == 'clean':
        strategy.data = {"groups": yaml.safe_load(tdgm.GROUPS_YAML)}

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
    def test_validate_deployment_action_full(self, *args):
        """Test the function that runs the validator class"""
        try:
            validate_deployment_action_full({
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
    def test_validate_deployment_action_full_cycle(self, *args):
        """Test the function that runs the validator class with a
        deployment strategy that has a cycle in the groups
        """
        with pytest.raises(ApiError) as apie:
            validate_deployment_action_full({
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
    def test_validate_deployment_action_full_missing_dep_strat(self, *args):
        """Test the function that runs the validator class with a missing
        deployment strategy - specified, but not present
        """
        with pytest.raises(ApiError) as apie:
            validate_deployment_action_full({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        assert apie.value.description == 'InvalidConfigurationDocuments'
        assert apie.value.error_list[0]['name'] == 'DocumentNotFoundError'

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean', ds_name='defaulted'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_deployment_action_full_default_dep_strat(self, *args):
        """Test the function that runs the validator class with a defaulted
        deployment strategy (not specified)
        """
        try:
            validate_deployment_action_full({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        except Exception:
            # any exception is a failure
            assert False

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean', ds_name='not-there'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_deployment_action_full_continue_failure(self, *args):
        """Test the function that runs the validator class with a missing
        deployment strategy (not specified), but continue-on-fail specified
        """
        try:
            validate_deployment_action_full({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1,
                'parameters': {'continue-on-fail': 'true'}
            })
        except Exception:
            # any exception is a failure
            assert False

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean', ds_name='not-there'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_deployment_action_basic_missing_dep_strat(self, *args):
        """Test the function that runs the validator class with a missing
        deployment strategy - specified, but not present. This should be
        ignored by the basic valdiator
        """
        try:
            validate_deployment_action_basic({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        except Exception:
            # any exception is a failure
            assert False

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    def test_validate_deployment_action_dep_strategy_exceptions(self, *args):
        """Test the function that runs the validator class for exceptions"""
        to_catch = [InvalidDeploymentGroupNodeLookupError,
                    InvalidDeploymentGroupError, DeploymentGroupCycleError]
        for exc in to_catch:
            with mock.patch(
                "shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_deployment_group_manager",
                side_effect=exc()
            ):
                with pytest.raises(ApiError) as apie:
                    validate_deployment_action_full({
                        'id': '123',
                        'name': 'deploy_site',
                        'committed_rev_id': 1
                    })
            assert apie.value.description == 'InvalidConfigurationDocuments'
            assert apie.value.error_list[0]['name'] == (exc.__name__)

    @mock.patch("shipyard_airflow.control.service_clients.deckhand_client",
                return_value=fake_dh_doc_client('clean'))
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_node_lookup",
                return_value=node_lookup)
    @mock.patch("shipyard_airflow.control.validators."
                "validate_deployment_strategy._get_deployment_group_manager",
                side_effect=TypeError())
    def test_validate_deployment_action_dep_strategy_exc_oth(self, *args):
        """Test the function that runs the validator class"""
        with pytest.raises(ApiError) as apie:
            validate_deployment_action_full({
                'id': '123',
                'name': 'deploy_site',
                'committed_rev_id': 1
            })
        assert apie.value.description == 'InvalidConfigurationDocuments'
        assert apie.value.error_list[0]['name'] == (
            'DocumentValidationProcessingError')

    def _action(self, params_field, comm_rev=1, allow=False):
        action = {
            'id': '123',
            'name': 'redeploy_server',
            'allow_intermediate_commits': allow
        }
        if comm_rev:
            action['committed_rev_id'] = comm_rev
        if params_field:
            action['parameters'] = params_field
        return action

    def test_validate_target_nodes(self, *args):
        """Test the validate_target_nodes/ValidateTargetNodes validator"""
        # pass - basic case
        validate_target_nodes(self._action({'target_nodes': ['node1']}))
        # missing parameter
        with pytest.raises(ApiError) as apie:
            validate_target_nodes(self._action(None))
        assert apie.value.title == 'Invalid target_nodes parameter'
        # no nodes
        with pytest.raises(ApiError) as apie:
            validate_target_nodes(self._action({'target_nodes': []}))
        assert apie.value.title == 'Invalid target_nodes parameter'
        # other parameter than target_nodes
        with pytest.raises(ApiError) as apie:
            validate_target_nodes(self._action({'no_nodes': ['what']}))
        assert apie.value.title == 'Invalid target_nodes parameter'
        # not a list-able target_nodes
        with pytest.raises(ApiError) as apie:
            validate_target_nodes(self._action({'target_nodes': pytest}))
        assert apie.value.title == 'Invalid target_nodes parameter'
        # not a list-able target_nodes
        with pytest.raises(ApiError) as apie:
            validate_target_nodes(
                self._action({'target_nodes': [{'not': 'string'}]})
            )
        assert apie.value.title == 'Invalid target_nodes parameter'

    def test_validate_committed_revision(self, *args):
        """Test the committed revision validator"""
        validate_committed_revision(self._action(None))
        with pytest.raises(ApiError) as apie:
            validate_committed_revision(self._action(None, comm_rev=None))
        assert apie.value.title == 'No committed configdocs'

    def test_validate_intermediate_commits(self, *args):
        """Test the intermediate commit validator"""
        ch_fail = CfgdHelperIntermediateCommit()
        ch_success = CfgdHelperIntermediateCommit(commits=False)
        validate_intermediate_commits(self._action(None), ch_success)
        with pytest.raises(ApiError) as apie:
            validate_intermediate_commits(self._action(None), ch_fail)
        assert apie.value.title == 'Intermediate commit detected'
        # bypass flag - no api error
        validate_intermediate_commits(
            self._action(None, allow=True), ch_fail
        )


class CfgdHelperIntermediateCommit():
    def __init__(self, commits=True):
        self.commits = commits

    def check_intermediate_commit(self):
        return self.commits
