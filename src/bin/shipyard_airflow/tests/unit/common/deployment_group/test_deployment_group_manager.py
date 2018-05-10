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
"""Tests to validate behavior of the classes in the deployment_group_manager
module
"""
import pytest
import yaml

from shipyard_airflow.common.deployment_group.deployment_group import (
    Stage
)
from shipyard_airflow.common.deployment_group.deployment_group_manager import (
    DeploymentGroupManager
)

from shipyard_airflow.common.deployment_group.errors import (
    DeploymentGroupCycleError, DeploymentGroupStageError,
    UnknownDeploymentGroupError, UnknownNodeError
)

from .node_lookup_stubs import node_lookup

GROUPS_YAML = """
- name: control-nodes
  critical: true
  depends_on:
    - ntp-node
  selectors:
    - node_names:
        - node1
        - node2
      node_labels: []
      node_tags: []
      rack_names:
        - rack1
  success_criteria:
    percent_successful_nodes: 100
- name: compute-nodes-1
  critical: false
  depends_on:
    - control-nodes
  selectors:
    - node_names: []
      node_labels:
        - compute:true
      rack_names:
        - rack2
      node_tags: []
  success_criteria:
    percent_successful_nodes: 50
- name: compute-nodes-2
  critical: false
  depends_on:
    - control-nodes
  selectors:
    - node_names: []
      node_labels:
        - compute:true
      rack_names:
        - rack3
      node_tags: []
  success_criteria:
    percent_successful_nodes: 50
- name: spare-compute-nodes
  critical: false
  depends_on:
    - compute-nodes-2
    - compute-nodes-1
  selectors:
    - node_names: []
      node_labels:
        - compute:true
      rack_names:
        - rack4
      node_tags: []
- name: all-compute-nodes
  critical: false
  depends_on:
    - compute-nodes-2
    - compute-nodes-1
    - spare-compute-nodes
  selectors:
    - node_names: []
      node_labels:
        - compute:true
      rack_names: []
      node_tags: []
- name: monitoring-nodes
  critical: false
  depends_on: []
  selectors:
    - node_names: []
      node_labels: []
      node_tags:
        - monitoring
      rack_names: []
  success_criteria:
    minimum_successful_nodes: 3
- name: ntp-node
  critical: true
  depends_on: []
  selectors:
    - node_names:
        - node3
      node_labels: []
      node_tags: []
      rack_names:
        - rack1
  success_criteria:
    minimum_successful_nodes: 1
"""

CYCLE_GROUPS_YAML = """
- name: group-a
  critical: true
  depends_on:
    - group-c
  selectors: []
- name: group-b
  critical: true
  depends_on:
    - group-a
  selectors: []
- name: group-c
  critical: true
  depends_on:
    - group-d
  selectors: []
- name: group-d
  critical: true
  depends_on:
    - group-a
  selectors: []

"""


class TestDeploymentGroupManager:
    def test_basic_class(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        assert dgm is not None
        # topological sort doesn't guarantee a specific order.
        assert dgm.get_next_group(Stage.PREPARED).name in ['ntp-node',
                                                           'monitoring-nodes']
        assert len(dgm._all_groups) == 7
        assert len(dgm._all_nodes) == 12
        for name, group in dgm._all_groups.items():
            assert name == group.name

    def test_cycle_error(self):
        with pytest.raises(DeploymentGroupCycleError) as ce:
            DeploymentGroupManager(yaml.safe_load(CYCLE_GROUPS_YAML),
                                   node_lookup)
        assert 'The following are involved' in str(ce)
        for g in ['group-a', 'group-c', 'group-d']:
            assert g in str(ce)
        assert 'group-b' not in str(ce)

    def test_no_next_group(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        assert dgm.get_next_group(Stage.DEPLOYED) is None

    def test_group_list(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        assert len(dgm.group_list()) == 7
        group_names = []
        for group in dgm.group_list():
            group_names.append(group.name)
        assert group_names == dgm._group_order

    def test_fail_unsuccessful_nodes(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        group = dgm._all_groups.get('control-nodes')
        dgm.fail_unsuccessful_nodes(group, [])
        assert not dgm.evaluate_group_succ_criteria('control-nodes',
                                                    Stage.DEPLOYED)
        assert group.stage == Stage.FAILED

    def test_reports(self, caplog):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        dgm.mark_node_deployed('node1')
        dgm.mark_node_prepared('node2')
        dgm.mark_node_failed('node3')
        dgm.mark_group_prepared('control-nodes')
        dgm.mark_group_deployed('control-nodes')
        dgm.mark_group_prepared('compute-nodes-1')
        dgm.mark_group_failed('compute-nodes-2')
        dgm.report_group_summary()
        assert "=====   Group Summary   =====" in caplog.text
        assert ("Group ntp-node [Critical] ended with stage: "
                "Stage.NOT_STARTED") in caplog.text
        caplog.clear()
        dgm.report_node_summary()
        assert "Nodes Stage.PREPARED: node2" in caplog.text
        assert "Nodes Stage.FAILED: node3" in caplog.text
        assert "===== End Node Summary =====" in caplog.text
        assert "It was the best of times" not in caplog.text

    def test_evaluate_group_succ_criteria(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        group = dgm._all_groups.get('control-nodes')

        nodes = ["node{}".format(i) for i in range(1, 12)]
        for node in nodes:
            dgm.mark_node_prepared(node)
        dgm.fail_unsuccessful_nodes(group, nodes)
        assert dgm.evaluate_group_succ_criteria('control-nodes',
                                                Stage.PREPARED)
        assert group.stage == Stage.PREPARED

        for node in nodes:
            dgm.mark_node_deployed(node)
        assert dgm.evaluate_group_succ_criteria('control-nodes',
                                                Stage.DEPLOYED)
        assert group.stage == Stage.DEPLOYED

    def test_critical_groups_failed(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        assert not dgm.critical_groups_failed()
        dgm.mark_group_failed('control-nodes')
        assert dgm.critical_groups_failed()

    def test_ordering_stages_flow_failure(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)

        group = dgm.get_next_group(Stage.PREPARED)
        if group.name == 'monitoring-nodes':
            dgm.mark_group_prepared(group.name)
            dgm.mark_group_deployed(group.name)
            group = dgm.get_next_group(Stage.PREPARED)
        if group.name == 'ntp-node':
            dgm.mark_group_failed(group.name)

        group = dgm.get_next_group(Stage.PREPARED)
        if group and group.name == 'monitoring-nodes':
            dgm.mark_group_prepared(group.name)
            dgm.mark_group_deployed(group.name)
            group = dgm.get_next_group(Stage.PREPARED)
        # all remaining groups should be failed, so no more to prepare
        for name, grp in dgm._all_groups.items():
            if (name == 'monitoring-nodes'):
                assert grp.stage == Stage.DEPLOYED
            else:
                assert grp.stage == Stage.FAILED
        assert group is None

    def test_deduplication(self):
        """all-compute-nodes is a duplicate of things it's dependent on, it
        should have no actionable nodes"""
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        acn = dgm._all_groups['all-compute-nodes']
        assert len(acn.actionable_nodes) == 0
        assert len(acn.full_nodes) == 6

    def test_bad_group_name_lookup(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        with pytest.raises(UnknownDeploymentGroupError) as udge:
            dgm.mark_group_prepared('Limburger Cheese')
        assert "Group name Limburger Cheese does not refer" in str(udge)

    def test_get_group_failures_for_stage_bad_input(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        with pytest.raises(DeploymentGroupStageError):
            dgm.get_group_failures_for_stage('group1', Stage.FAILED)

    def test_get_group_failures_for_stage(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        dgm._all_nodes = {'node%d' % x: Stage.DEPLOYED for x in range(1, 13)}

        for group_name in dgm._all_groups:
            assert not dgm.get_group_failures_for_stage(group_name,
                                                        Stage.DEPLOYED)
            assert not dgm.get_group_failures_for_stage(group_name,
                                                        Stage.PREPARED)

        dgm._all_nodes = {'node%d' % x: Stage.PREPARED for x in range(1, 13)}

        for group_name in dgm._all_groups:
            assert not dgm.get_group_failures_for_stage(group_name,
                                                        Stage.PREPARED)

        for group_name in ['compute-nodes-1',
                           'monitoring-nodes',
                           'compute-nodes-2',
                           'control-nodes',
                           'ntp-node']:
            # assert that these have a failure
            assert dgm.get_group_failures_for_stage(group_name, Stage.DEPLOYED)

        dgm._all_nodes = {
            'node1': Stage.FAILED,
            'node2': Stage.PREPARED,
            'node3': Stage.FAILED,
            'node4': Stage.PREPARED,
            'node5': Stage.FAILED,
            'node6': Stage.PREPARED,
            'node7': Stage.FAILED,
            'node8': Stage.PREPARED,
            'node9': Stage.FAILED,
            'node10': Stage.PREPARED,
            'node11': Stage.FAILED,
            'node12': Stage.PREPARED,
        }
        for group_name in dgm._all_groups:
            scf = dgm.get_group_failures_for_stage(group_name,
                                                   Stage.PREPARED)
            if group_name == 'monitoring-nodes':
                assert scf[0] == {'criteria': 'minimum_successful_nodes',
                                  'needed': 3,
                                  'actual': 2}
            if group_name == 'control-nodes':
                assert scf[0] == {'criteria': 'percent_successful_nodes',
                                  'needed': 100,
                                  'actual': 50.0}
            if group_name == 'ntp-node':
                assert scf[0] == {'criteria': 'minimum_successful_nodes',
                                  'needed': 1,
                                  'actual': 0}

    def test_mark_node_deployed(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        dgm.mark_node_deployed('node1')
        assert dgm.get_nodes(Stage.DEPLOYED) == ['node1']

    def test_mark_node_prepared(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        dgm.mark_node_prepared('node1')
        assert dgm.get_nodes(Stage.PREPARED) == ['node1']

    def test_mark_node_failed(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        dgm.mark_node_failed('node1')
        assert dgm.get_nodes(Stage.FAILED) == ['node1']

    def test_mark_node_failed_unknown(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        with pytest.raises(UnknownNodeError):
            dgm.mark_node_failed('not_node')

    def test_get_nodes_all(self):
        dgm = DeploymentGroupManager(yaml.safe_load(GROUPS_YAML), node_lookup)
        assert set(dgm.get_nodes()) == set(
            ['node1', 'node2', 'node3', 'node4', 'node5', 'node6', 'node7',
             'node8', 'node9', 'node10', 'node11', 'node12']
        )
