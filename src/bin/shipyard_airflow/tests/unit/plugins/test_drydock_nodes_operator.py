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
"""Tests for drydock_nodes operator functions"""
import copy
import os
from unittest import mock

import pytest
import yaml

from airflow.exceptions import AirflowException

from shipyard_airflow.common.deployment_group.deployment_group import (
    DeploymentGroup,
    Stage
)

from shipyard_airflow.common.deployment_group.deployment_group_manager import (
    DeploymentGroupManager
)

from shipyard_airflow.plugins.drydock_nodes import (
    _default_deployment_strategy,
    _gen_node_name_filter,
    DrydockNodesOperator,
    _process_deployment_groups,
    QueryTaskResult
)

from shipyard_airflow.plugins.deployment_configuration_operator import (
    DeploymentConfigurationOperator
)

import tests.unit.common.deployment_group.test_deployment_group_manager as tdgm
from tests.unit.common.deployment_group.node_lookup_stubs import node_lookup

CONF_FILE = os.path.join(os.path.dirname(__file__), 'test.conf')


def _fake_deployment_group_manager(cgf_bool):

    def dgm_func(group_dict_list, node_lookup):
        dgm_mock = mock.MagicMock()
        dgm_mock.critical_groups_failed = mock.Mock(return_value=cgf_bool)
        return dgm_mock
    return dgm_func(None, None)


GROUP_DICT = {
    'name': 'control-nodes',
    'critical': True,
    'depends_on': ['ntp-node'],
    'selectors': [
        {
            'node_names': ['node1', 'node2', 'node3', 'node4', 'node5'],
            'node_labels': [],
            'node_tags': [],
            'rack_names': [],
        },
    ],
    'success_criteria': {
        'percent_successful_nodes': 90,
        'minimum_successful_nodes': 3,
        'maximum_failed_nodes': 1,
    },
}

TASK_RESULT = QueryTaskResult('t1', 'tn')
TASK_RESULT.successes = ['node1', 'node2', 'node3']

# The top level result should have all successes specified
TASK_DICT = {
    '0': {
        'result': {
            'successes': ['node1', 'node2', 'node3'],
            'status': 'success',
        },
        'subtask_id_list': ['1'],
        'status': 'complete'
    },
    '1': {
        'result': {
            'successes': ['node3'],
            'status': 'success',
        },
        'subtask_id_list': ['2', '3'],
        'status': 'complete'
    },
    '2': {
        'result': {
            'successes': ['node2'],
            'status': 'success',
            'details': {'messageList': [
                {
                    'context': 'node2',
                    'context_type': 'node',
                    'error': False,
                    'extra': '{}',
                    'message': 'Warning node2 is slow',
                    'ts': '2018-06-14 22:41:08.195036'
                },
                {
                    'context': 'node2',
                    'context_type': 'node',
                },
            ]},
        },
        'subtask_id_list': [],
        'status': 'complete',
    },
    '3': {
        'result': {
            'status': 'success',
            'details': {'messageList': [
                {
                    'context': 'task 3',
                    'context_type': 'task',
                    'error': False,
                    'extra': '{}',
                    'message': 'Started subtask 3 for action apply_node_stuff',
                    'ts': '2018-06-14 22:41:08.195036'
                },
                {
                    'context': 'task 3',
                    'context_type': 'task',
                    'error': False,
                    'extra': '{}',
                    'message': 'Ended subtask 3 for action apply_node_stuff',
                    'ts': '2018-06-14 22:41:08.195036'
                },
            ]},
        },
        'subtask_id_list': [],
        'status': 'complete',
    },
    '99': {
        'result': {
            'status': 'failure',
            'successes': ['node98', 'node97'],
            'failures': ['node99'],
            'details': {'messageList': [
                {
                    'context': 'task 99',
                    'context_type': 'task',
                    'error': False,
                    'extra': '{}',
                    'message': 'Started subtask 99 for action do_things',
                    'ts': '2018-06-14 22:41:08.195036'
                },
                {
                    'context': 'task 99',
                    'context_type': 'task',
                    'error': True,
                    'extra': '{}',
                    'message': 'Task 99 broke things',
                    'ts': '2018-06-14 22:41:08.195036'
                },
            ]},
        },
        'subtask_id_list': ['2'],
    },
}

DEP_STRAT = {'groups': yaml.safe_load(tdgm.GROUPS_YAML)}


def _fake_setup_ds(self):
    self.strategy = DEP_STRAT


def _fake_get_task_dict(task_id):
    return TASK_DICT[task_id]


def _gen_pe_func(mode, stand_alone=False):
    """Gen a function to play the role of prepare or deploy function

    :param mode: 'all-success', 'all-fail'
    :param stand_alone: indicate to make this a "self" or non-self
        function. During mocking for direct calls with this function,
        stand_alone needs to be True. When patching the DrydockNodesOperator
        object, it needs to be false, so that the right amount of "self"
        matches the invocation.
    """
    def _func(group):
        qtr = QueryTaskResult('ti', 'tn')
        if mode == 'all-success':
            qtr.successes.extend(group.actionable_nodes)
        if mode == 'all-fail':
            # no new sucesses
            pass
        return qtr

    def _func_self(self, group):
        return _func(group)

    if stand_alone:
        return _func
    else:
        return _func_self


class TestDrydockNodesOperator:
    def test_default_deployment_strategy(self):
        """Assert that the default deployment strategy is named default, is
        critical, has no selector values, and an all-or-nothing success
        criteria
        """
        s = _default_deployment_strategy()
        assert s['groups'][0]['name'] == 'default'
        assert s['groups'][0]['critical']
        assert s['groups'][0]['selectors'][0]['node_names'] == []
        assert s['groups'][0]['selectors'][0]['node_labels'] == []
        assert s['groups'][0]['selectors'][0]['node_tags'] == []
        assert s['groups'][0]['selectors'][0]['rack_names'] == []
        assert s['groups'][0]['success_criteria'] == {
            'percent_successful_nodes': 100
        }

    def test_gen_node_name_filter(self):
        """Test that a node name filter with only node_names is created"""
        nodes = ['node1', 'node2']
        f = _gen_node_name_filter(nodes)
        assert f['filter_set'][0]['node_names'] == nodes
        assert len(f['filter_set']) == 1

    def test_init_DrydockNodesOperator(self):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        assert op is not None

    @mock.patch.object(DrydockNodesOperator, "get_unique_doc")
    def test_setup_deployment_strategy(self, udoc):
        """Assert that the base class method get_unique_doc would be invoked
        """
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.dc = copy.deepcopy(
            DeploymentConfigurationOperator.config_keys_defaults
        )
        op.dc['physical_provisioner.deployment_strategy'] = 'taco-salad'
        op._setup_deployment_strategy()
        udoc.assert_called_once_with(
            name='taco-salad',
            schema="shipyard/DeploymentStrategy/v1"
        )

    @mock.patch("shipyard_airflow.plugins.drydock_nodes."
                "_get_deployment_group_manager",
                return_value=_fake_deployment_group_manager(cgf_bool=False))
    @mock.patch("shipyard_airflow.plugins.drydock_nodes."
                "_process_deployment_groups", return_value=True)
    @mock.patch("shipyard_airflow.plugins.drydock_nodes._get_node_lookup",
                return_value=mock.MagicMock())
    def test_do_execute(self, nl, pdg, get_dgm, caplog):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.dc = copy.deepcopy(
            DeploymentConfigurationOperator.config_keys_defaults
        )
        op.design_ref = {}
        op.do_execute()
        assert get_dgm.call_count == 1
        assert nl.call_count == 1
        assert pdg.call_count == 1
        assert "critical groups have met their success criteria" in caplog.text

    @mock.patch("shipyard_airflow.plugins.drydock_nodes."
                "_get_deployment_group_manager",
                return_value=_fake_deployment_group_manager(cgf_bool=True))
    @mock.patch("shipyard_airflow.plugins.drydock_nodes."
                "_process_deployment_groups", return_value=True)
    @mock.patch("shipyard_airflow.plugins.drydock_nodes._get_node_lookup",
                return_value=mock.MagicMock())
    def test_do_execute_exception(self, nl, pdg, get_dgm):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        with pytest.raises(AirflowException):
            op.dc = copy.deepcopy(
                DeploymentConfigurationOperator.config_keys_defaults
            )
            op.design_ref = {}
            op.do_execute()

        assert get_dgm.call_count == 1
        assert nl.call_count == 1
        assert pdg.call_count == 1

    def test_execute_prepare(self):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.dc = copy.deepcopy(
            DeploymentConfigurationOperator.config_keys_defaults
        )
        op._setup_configured_values()
        op._execute_task = mock.MagicMock(return_value=TASK_RESULT)
        group = DeploymentGroup(GROUP_DICT, mock.MagicMock())
        group.actionable_nodes = ['node1', 'node2', 'node3']
        op._execute_prepare(group)
        assert op._execute_task.call_count == 1

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "check_node_status", return_value=[])
    def test_execute_deployment(self, cns):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.dc = copy.deepcopy(
            DeploymentConfigurationOperator.config_keys_defaults
        )
        op._setup_configured_values()
        op._execute_task = mock.MagicMock(return_value=TASK_RESULT)
        op.join_wait = 0
        group = DeploymentGroup(GROUP_DICT, mock.MagicMock())
        group.actionable_nodes = ['node1', 'node2', 'node3']
        op._execute_deployment(group)
        assert op._execute_task.call_count == 1
        assert cns.call_count == 1

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "check_node_status", return_value=['node2', 'node4'])
    def test_execute_deployment_k8s_fail(self, cns, caplog):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.dc = copy.deepcopy(
            DeploymentConfigurationOperator.config_keys_defaults
        )
        op._setup_configured_values()
        op._execute_task = mock.MagicMock(return_value=TASK_RESULT)
        op.join_wait = 0
        group = DeploymentGroup(GROUP_DICT, mock.MagicMock())
        group.actionable_nodes = ['node1', 'node2', 'node3']
        task_res = op._execute_deployment(group)
        assert op._execute_task.call_count == 1
        assert cns.call_count == 1
        assert 'node4 failed to join Kubernetes' in caplog.text
        assert len(task_res.successes) == 2

    def test_get_successess_for_task(self):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.get_task_dict = _fake_get_task_dict
        s = op._get_successes_for_task('0')
        for i in range(1, 3):
            assert "node{}".format(i) in s

    def test_get_successess_for_task_more_logging(self):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.get_task_dict = _fake_get_task_dict
        s = op._get_successes_for_task('99')
        for i in range(97, 98):
            assert "node{}".format(i) in s
        assert "node2" not in s

    def test_process_deployment_groups(self):
        """Test the core processing loop of the drydock_nodes module"""
        dgm = DeploymentGroupManager(
            yaml.safe_load(tdgm.GROUPS_YAML),
            node_lookup
        )
        _process_deployment_groups(
            dgm,
            _gen_pe_func('all-success', stand_alone=True),
            _gen_pe_func('all-success', stand_alone=True))
        assert not dgm.critical_groups_failed()
        for group in dgm.group_list():
            assert dgm.evaluate_group_succ_criteria(group.name, Stage.DEPLOYED)

    def test_process_deployment_groups_dep_fail(self):
        """Test the core processing loop of the drydock_nodes module"""
        dgm = DeploymentGroupManager(
            yaml.safe_load(tdgm.GROUPS_YAML),
            node_lookup
        )
        _process_deployment_groups(
            dgm,
            _gen_pe_func('all-success', stand_alone=True),
            _gen_pe_func('all-fail', stand_alone=True))
        assert dgm.critical_groups_failed()
        for group in dgm.group_list():
            assert group.stage == Stage.FAILED
        dgm.report_group_summary()
        dgm.report_node_summary()

    def test_process_deployment_groups_prep_fail(self):
        """Test the core processing loop of the drydock_nodes module"""
        dgm = DeploymentGroupManager(
            yaml.safe_load(tdgm.GROUPS_YAML),
            node_lookup
        )
        _process_deployment_groups(
            dgm,
            _gen_pe_func('all-fail', stand_alone=True),
            _gen_pe_func('all-success', stand_alone=True))
        assert dgm.critical_groups_failed()
        for group in dgm.group_list():
            assert group.stage == Stage.FAILED
        dgm.report_group_summary()
        dgm.report_node_summary()

    @mock.patch("shipyard_airflow.plugins.drydock_nodes._get_node_lookup",
                return_value=node_lookup)
    @mock.patch.object(
        DrydockNodesOperator,
        '_execute_prepare',
        new=_gen_pe_func('all-success')
    )
    @mock.patch.object(
        DrydockNodesOperator,
        '_execute_deployment',
        new=_gen_pe_func('all-success')
    )
    @mock.patch.object(DrydockNodesOperator, '_setup_deployment_strategy',
                       new=_fake_setup_ds)
    def test_do_execute_with_dgm(self, nl, caplog):
        op = DrydockNodesOperator(main_dag_name="main",
                                  shipyard_conf=CONF_FILE,
                                  task_id="t1")
        op.dc = copy.deepcopy(
            DeploymentConfigurationOperator.config_keys_defaults
        )
        op.design_ref = {"a": "b"}
        op.do_execute()
        assert "critical groups have met their success criteria" in caplog.text

    # TODO (bryan-strassner) test for _execute_task
