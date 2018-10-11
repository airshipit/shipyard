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
"""An additional test using a "real" use case to ensure that node filters
being produced are as expected before they would be sent to Drydock for
resolution of nodes from the filter.
"""
import logging
import yaml

from shipyard_airflow.common.deployment_group.deployment_group import (
    Stage
)
from shipyard_airflow.common.deployment_group.deployment_group_manager import (
    DeploymentGroupManager
)
from shipyard_airflow.common.deployment_group.node_lookup import (
    _generate_node_filter,
    _validate_selectors
)


LOG = logging.getLogger(__name__)

INPUT_YAML = """
---
schema: shipyard/DeploymentStrategy/v1
metadata:
  schema: metadata/Document/v1
  replacement: true
  name: deployment-strategy
  layeringDefinition:
    abstract: false
    layer: site
    parentSelector:
      name: deployment-strategy-global
    actions:
      - method: replace
        path: .
  storagePolicy: cleartext
  replacement: true
data:
  groups:
    - name: masters
      critical: true
      depends_on: []
      selectors:
        - node_names: []
          node_labels: []
          node_tags:
            - masters
          rack_names: []
      success_criteria:
        percent_successful_nodes: 100
    - name: worker_group_0
      critical: false
      depends_on:
        - masters
      selectors:
        - node_names: []
          node_labels: []
          node_tags: []
          rack_names:
            - 'RACK03'
            - 'RACK04'
    - name: worker_group_1
      critical: false
      depends_on:
        - masters
      selectors:
        - node_names: []
          node_labels: []
          node_tags: []
          rack_names:
            - 'RACK05'
            - 'RACK06'
    - name: workers
      critical: true
      depends_on:
        - worker_group_0
        - worker_group_1
      selectors:
        - node_names: []
          node_labels: []
          node_tags:
            - workers
          rack_names: []
      success_criteria:
        percent_successful_nodes: 60
...
"""

nf_masters = {
    'filter_set_type':
    'union',
    'filter_set': [{
        'filter_type': 'intersection',
        'node_names': [],
        'node_tags': ['masters'],
        'node_labels': {},
        'rack_names': []
    }]
}
nf_rack_03_04 = {
    'filter_set_type':
    'union',
    'filter_set': [{
        'filter_type': 'intersection',
        'node_names': [],
        'node_tags': [],
        'node_labels': {},
        'rack_names': ['RACK03', 'RACK04']
    }]
}
nf_rack_05_06 = {
    'filter_set_type':
    'union',
    'filter_set': [{
        'filter_type': 'intersection',
        'node_names': [],
        'node_tags': [],
        'node_labels': {},
        'rack_names': ['RACK05', 'RACK06']
    }]
}
nf_workers = {
    'filter_set_type':
    'union',
    'filter_set': [{
        'filter_type': 'intersection',
        'node_names': [],
        'node_tags': ['workers'],
        'node_labels': {},
        'rack_names': []
    }]
}


def node_lookup(selectors):
    """Assert things about the input and expected response based on the yaml
    above
    """
    _validate_selectors(selectors)
    nf = _generate_node_filter(selectors)
    LOG.info(nf)
    nodes = []
    for selector in selectors:
        if selector.rack_names:
            assert len(selector.rack_names) == 2
            assert len(nf['filter_set'][0]['rack_names']) == 2
            assert len(nf['filter_set'][0]['node_names']) == 0
            assert len(nf['filter_set'][0]['node_tags']) == 0
            assert len(nf['filter_set'][0]['node_labels']) == 0
            if "RACK03" in selector.rack_names:
                assert nf == nf_rack_03_04
            if "RACK05" in selector.rack_names:
                assert nf == nf_rack_05_06
            for rack in selector.rack_names:
                nodes.append(rack + "node1")
        if 'masters' in selector.node_tags:
            assert len(nf['filter_set'][0]['rack_names']) == 0
            assert len(nf['filter_set'][0]['node_names']) == 0
            assert len(nf['filter_set'][0]['node_tags']) == 1
            assert len(nf['filter_set'][0]['node_labels']) == 0
            assert nf == nf_masters
            nodes.append("master1")
            nodes.append("master2")
        if 'workers' in selector.node_tags:
            assert len(nf['filter_set'][0]['rack_names']) == 0
            assert len(nf['filter_set'][0]['node_names']) == 0
            assert len(nf['filter_set'][0]['node_tags']) == 1
            assert len(nf['filter_set'][0]['node_labels']) == 0
            assert nf == nf_workers
            nodes.append("RACK06node1")
            nodes.append("RACK05node1")
            nodes.append("RACK04node1")
            nodes.append("RACK03node1")
    return nodes


class TestDeploymentGroupManagerRackNames:
    def test_dgm(self):
        all_yaml_dict = yaml.safe_load(INPUT_YAML)
        group_dict_list = all_yaml_dict['data']['groups']

        dgm = DeploymentGroupManager(group_dict_list, node_lookup)
        assert dgm is not None
        # topological sort doesn't guarantee a specific order.
        assert dgm.get_next_group(Stage.PREPARED).name == 'masters'
        assert len(dgm._all_groups) == 4
        assert len(dgm._all_nodes) == 6
