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
"""Tests for the default node_lookup provided with the deployment group
functionality.
"""
import mock

import pytest

from shipyard_airflow.common.deployment_group.deployment_group import (
    GroupNodeSelector
)
from shipyard_airflow.common.deployment_group.errors import (
    InvalidDeploymentGroupNodeLookupError
)
from shipyard_airflow.common.deployment_group.node_lookup import (
    NodeLookup, _generate_node_filter, _validate_selectors
)


class TestNodeLookup:
    def test_validate_selectors(self):
        """Tests the _validate_selectors function"""
        try:
            _validate_selectors([GroupNodeSelector({})])
            _validate_selectors([])
        except:
            # No exceptions expected.
            assert False

        with pytest.raises(InvalidDeploymentGroupNodeLookupError) as idgnle:
            _validate_selectors(None)
        assert "iterable of GroupNodeSelectors" in str(idgnle.value)

        with pytest.raises(InvalidDeploymentGroupNodeLookupError) as idgnle:
            _validate_selectors(["bad!"])
        assert "all input elements in the selectors" in str(idgnle.value)

        with pytest.raises(InvalidDeploymentGroupNodeLookupError) as idgnle:
            _validate_selectors(["bad!", "also bad!"])
        assert "all input elements in the selectors" in str(idgnle.value)

        with pytest.raises(InvalidDeploymentGroupNodeLookupError) as idgnle:
            _validate_selectors([GroupNodeSelector({}), "bad!"])
        assert "all input elements in the selectors" in str(idgnle.value)

    def test_generate_node_filter(self):
        """Tests the _generate_node_filter function"""
        sel = GroupNodeSelector({
            'node_names': [],
            'node_labels': ['label1:label1'],
            'node_tags': ['tag1', 'tag2'],
            'rack_names': ['rack3', 'rack1'],
        })
        nf = _generate_node_filter([sel])
        assert nf == {
            'filter_set': [{
                'filter_type': 'intersection',
                'node_names': [],
                'node_tags': ['tag1', 'tag2'],
                'rack_names': ['rack3', 'rack1'],
                'node_labels': {'label1': 'label1'}}
            ],
            'filter_set_type': 'union'
        }

        sel2 = GroupNodeSelector({
            'node_names': ['node1', 'node2', 'node3', 'node4', 'node5'],
            'node_labels': ['label1:label1', 'label2:label2'],
            'node_tags': ['tag1', 'tag2'],
            'rack_names': ['rack3', 'rack1'],
        })
        nf = _generate_node_filter([sel, sel2])
        assert nf == {
            'filter_set': [
                {
                    'filter_type': 'intersection',
                    'node_names': [],
                    'node_tags': ['tag1', 'tag2'],
                    'rack_names': ['rack3', 'rack1'],
                    'node_labels': {'label1': 'label1'}
                },
                {
                    'filter_type': 'intersection',
                    'node_names': ['node1', 'node2', 'node3', 'node4',
                                   'node5'],
                    'node_tags': ['tag1', 'tag2'],
                    'rack_names': ['rack3', 'rack1'],
                    'node_labels': {'label1': 'label1', 'label2': 'label2'}
                }
            ],
            'filter_set_type': 'union'
        }

        sel3 = GroupNodeSelector({})
        sel4 = GroupNodeSelector({
            'node_names': [],
            'node_labels': [],
            'node_tags': [],
            'rack_names': [],
        })
        nf = _generate_node_filter([sel, sel3, sel4])
        assert nf == {
            'filter_set': [{
                'filter_type': 'intersection',
                'node_names': [],
                'node_tags': ['tag1', 'tag2'],
                'rack_names': ['rack3', 'rack1'],
                'node_labels': {'label1': 'label1'}}
            ],
            'filter_set_type': 'union'
        }

        nf = _generate_node_filter([sel3, sel4])
        assert nf is None

    @mock.patch('shipyard_airflow.common.deployment_group.node_lookup'
                '._get_nodes_for_filter', return_value=['node1', 'node2'])
    def test_NodeLookup_lookup(self, *args):
        """Test the functionality of the setup and lookup functions"""
        nl = NodeLookup(mock.MagicMock(), {"design": "ref"})

        assert nl.design_ref == {"design": "ref"}
        assert nl.drydock_client

        sel = GroupNodeSelector({
            'node_names': [],
            'node_labels': ['label1:label1'],
            'node_tags': ['tag1', 'tag2'],
            'rack_names': ['rack3', 'rack1'],
        })

        resp = nl.lookup([sel])
        assert resp == ['node1', 'node2']

    def test_NodeLookup_lookup_missing_design_ref(self):
        """Test the functionality of the setup and lookup functions"""
        with pytest.raises(InvalidDeploymentGroupNodeLookupError) as idgnle:
            NodeLookup(mock.MagicMock(), {})
        assert 'An incomplete design ref' in str(idgnle.value)
