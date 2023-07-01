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
"""Tests to validate behavior of the classes in the deployment_group module"""
import pytest
import yaml

from shipyard_airflow.common.deployment_group.deployment_group import (
    DeploymentGroup, Stage, check_label_format
)
from shipyard_airflow.common.deployment_group.errors import (
    DeploymentGroupLabelFormatError, DeploymentGroupStageError,
    InvalidDeploymentGroupError, InvalidDeploymentGroupNodeLookupError
)

from .node_lookup_stubs import node_lookup
from .node_lookup_stubs import crummy_node_lookup
from .node_lookup_stubs import broken_node_lookup_1
from .node_lookup_stubs import broken_node_lookup_2


_GROUP_YAML_1 = """
name: control-nodes
critical: true
depends_on:
  - ntp-node
selectors:
  - node_names: []
    node_labels: []
    node_tags:
      - tag1
    rack_names:
      - rack3
success_criteria:
  percent_successful_nodes: 90
  minimum_successful_nodes: 3
  maximum_failed_nodes: 1
"""

_GROUP_YAML_MULTI_SELECTOR = """
name: control-nodes
critical: true
depends_on:
  - ntp-node
selectors:
  - node_names: []
    node_labels: []
    node_tags:
      - tag1
    rack_names:
      - rack3
  - node_names: []
    node_labels:
      - label1:label1
    node_tags: []
    rack_names:
      - rack3
      - rack4
success_criteria:
  percent_successful_nodes: 79
  minimum_successful_nodes: 3
  maximum_failed_nodes: 1
"""

_GROUP_YAML_EXCLUDES_ALL = """
name: control-nodes
critical: true
depends_on:
  - ntp-node
selectors:
  - node_names: []
    node_labels: []
    node_tags:
      - tag2
    rack_names:
      - rack4
success_criteria:
  percent_successful_nodes: 90
  minimum_successful_nodes: 3
  maximum_failed_nodes: 1
"""

_GROUP_YAML_MISSING = """
name: control-nodes
"""

_GROUP_YAML_NO_SUCC_CRITERIA = """
name: control-nodes
critical: true
depends_on:
  - ntp-node
selectors:
  - node_names: []
    node_labels:
      - label1:label1
    node_tags: []
    rack_names:
      - rack3
      - rack4
"""

_GROUP_YAML_MINIMAL_SUCC_CRITERIA = """
name: control-nodes
critical: true
depends_on:
  - ntp-node
selectors:
  - node_names: []
    node_labels: []
    node_tags:
      - tag1
    rack_names:
      - rack3
  - node_names: []
    node_labels:
      - label1:label1
    node_tags: []
    rack_names:
      - rack3
      - rack4
success_criteria:
  maximum_failed_nodes: 1
"""


_GROUP_YAML_ALL_SELECTOR = """
name: control-nodes
critical: true
depends_on:
  - ntp-node
selectors: []
"""

_GROUP_YAML_ALL_SELECTOR_2 = """
name: control-nodes
critical: true
depends_on:
  - ntp-node
selectors: [
    node_names: []
]
"""


class TestDeploymentGroup:
    def test_basic_class(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_1), node_lookup)
        assert set(dg.full_nodes) == {'node8'}
        assert dg.critical
        assert dg.name == "control-nodes"
        assert set(dg.depends_on) == {"ntp-node"}
        assert len(dg.selectors) == 1
        assert not dg.success_criteria._always_succeed
        assert dg.success_criteria.pct_succ_nodes == 90
        assert dg.success_criteria.min_succ_nodes == 3
        assert dg.success_criteria.max_failed_nodes == 1
        assert dg.stage == Stage.NOT_STARTED

    def test_basic_class_multi_selector(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_MULTI_SELECTOR),
                             node_lookup)
        assert set(dg.full_nodes) == {'node7', 'node8', 'node9', 'node11'}
        assert dg.selectors[0].get_node_labels_as_dict() == {}
        assert dg.selectors[1].get_node_labels_as_dict() == {
            'label1': 'label1'
        }

    def test_basic_class_missing_req(self):
        with pytest.raises(InvalidDeploymentGroupError):
            DeploymentGroup(yaml.safe_load(_GROUP_YAML_MISSING),
                            node_lookup)

    def test_basic_class_no_succ_criteria(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_NO_SUCC_CRITERIA),
                             node_lookup)
        assert dg.success_criteria._always_succeed
        assert not dg.get_failed_success_criteria([])

    def test_succ_criteria_success(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_MULTI_SELECTOR),
                             node_lookup)
        assert set(dg.full_nodes) == {'node7', 'node8', 'node9', 'node11'}
        assert not dg.get_failed_success_criteria(
            success_node_list=['node7', 'node8', 'node11', 'node9']
        )

    def test_succ_criteria_minimal_criteria(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_MINIMAL_SUCC_CRITERIA),
                             node_lookup)
        assert set(dg.full_nodes) == {'node7', 'node8', 'node9', 'node11'}
        assert not dg.get_failed_success_criteria(
            success_node_list=['node8', 'node11', 'node9']
        )

    def test_succ_criteria_failure(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_MULTI_SELECTOR),
                             node_lookup)
        assert set(dg.full_nodes) == {'node7', 'node8', 'node9', 'node11'}
        failed = dg.get_failed_success_criteria(
            success_node_list=['node8', 'node11', 'node9']
        )
        assert len(failed) == 1
        assert failed[0] == {'actual': 75.0,
                             'criteria': 'percent_successful_nodes',
                             'needed': 79}

    def test_all_selector_group(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_ALL_SELECTOR),
                             node_lookup)
        assert dg.selectors[0].all_selector
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_ALL_SELECTOR_2),
                             node_lookup)
        assert dg.selectors[0].all_selector

    def test_selector_excludes_all(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_EXCLUDES_ALL),
                             node_lookup)
        assert len(dg.full_nodes) == 0

    def test_handle_none_node_lookup(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_1),
                             crummy_node_lookup)
        assert len(dg.full_nodes) == 0

    def test_handle_broken_node_lookup(self):
        with pytest.raises(InvalidDeploymentGroupNodeLookupError) as err:
            DeploymentGroup(yaml.safe_load(_GROUP_YAML_1),
                            broken_node_lookup_1)
        assert err.match("is not an iterable")

        with pytest.raises(InvalidDeploymentGroupNodeLookupError) as err:
            DeploymentGroup(yaml.safe_load(_GROUP_YAML_1),
                            broken_node_lookup_2)
        assert err.match("is not all strings")

    def test_set_stage(self):
        dg = DeploymentGroup(yaml.safe_load(_GROUP_YAML_ALL_SELECTOR),
                             node_lookup)
        with pytest.raises(DeploymentGroupStageError):
            dg.stage = Stage.DEPLOYED
        dg.stage = Stage.PREPARED
        assert dg.stage == Stage.PREPARED
        dg.stage = Stage.DEPLOYED
        assert dg.stage == Stage.DEPLOYED


class TestStage:
    def test_is_complete(self):
        assert not Stage.is_complete(Stage.NOT_STARTED)
        assert not Stage.is_complete(Stage.PREPARED)
        assert Stage.is_complete(Stage.DEPLOYED)
        assert Stage.is_complete(Stage.FAILED)

    def test_previous_stage(self):
        assert Stage.previous_stage(Stage.NOT_STARTED) == []
        assert Stage.previous_stage(Stage.PREPARED) == [Stage.NOT_STARTED]
        assert Stage.previous_stage(Stage.DEPLOYED) == [Stage.PREPARED]
        assert Stage.previous_stage(Stage.FAILED) == [Stage.NOT_STARTED,
                                                      Stage.PREPARED]
        with pytest.raises(DeploymentGroupStageError) as de:
            Stage.previous_stage('Chickens and Turkeys')
        assert de.match("Chickens and Turkeys is not a valid stage")


class TestCheckLabelFormat:
    def test_check_label_format(self):
        with pytest.raises(DeploymentGroupLabelFormatError) as dglfe:
            check_label_format("thisthat")
        assert "thisthat is formatted incorrectly. One" in str(dglfe.value)

        with pytest.raises(DeploymentGroupLabelFormatError) as dglfe:
            check_label_format("")
        assert " is formatted incorrectly. One" in str(dglfe.value)

        with pytest.raises(DeploymentGroupLabelFormatError) as dglfe:
            check_label_format(":::")
        assert "::: is formatted incorrectly. One" in str(dglfe.value)

        with pytest.raises(DeploymentGroupLabelFormatError) as dglfe:
            check_label_format("this:that:another")
        assert ("this:that:another is formatted incorrectly. "
                "One") in str(dglfe.value)

        with pytest.raises(DeploymentGroupLabelFormatError) as dglfe:
            check_label_format("this:    ")
        assert "this:     is formatted incorrectly. The" in str(dglfe.value)

        # no exceptions - these are good
        check_label_format("this:that")
        check_label_format(" this : that ")
