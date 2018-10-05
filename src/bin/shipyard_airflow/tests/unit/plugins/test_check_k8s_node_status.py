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
"""Tests for check_k8s_node_status functions"""
from unittest import mock

from shipyard_airflow.plugins.check_k8s_node_status import (
    check_node_status
)


class MockNodeStatus:
    """A fake response object used to simulate a k8s node status item"""
    def __init__(self, name, status, message):
        self.metadata = mock.MagicMock()
        self.metadata.name = name
        self.item = mock.MagicMock()
        self.item.status = status
        self.item.message = message
        self.status = mock.MagicMock()
        self.status.conditions = [self.item]


class MalformedNodeStatus:
    """A malformed response object used to simulate a k8s node status item

    Accepts a name, if the name field should be formed correctly.
    """
    def __init__(self, name=None):
        if name:
            self.metadata = mock.MagicMock()
            self.metadata.name = name

        self.status = mock.MagicMock()
        self.status.conditions = "broken"


def gen_check_node_status(response_dict):
    """Generate a function that will return the requested response dict

    :param response_dict: the set of responses to return
    """
    class _StatefulResponder:
        def __init__(self, res_dict=response_dict):
            self.res_dict = res_dict
            self.invocation = 0

        def responder(self):
            ret = mock.MagicMock()
            if str(self.invocation) in self.res_dict:
                ret.items = self.res_dict.get(str(self.invocation))
            else:
                ret.items = self.res_dict.get('final')
            self.invocation += 1
            return ret
    sr = _StatefulResponder()
    return sr.responder


# Node names used in these tests will be represented by a letter and number
# E.g. a1, a2, a3, b1, b2, etc.

# The following dictionaries are sequences of response objects that are
# returned from the _get_all_k8s_node_status substitute method.

# Successful single invocation response. 3 nodes, a1, b1, c1, all ready on the
# first pass
INV_SEQ_A = {
    'final': [
        MockNodeStatus('a1', 'True', 'Ready'),
        MockNodeStatus('b1', 'True', 'Ready'),
        MockNodeStatus('c1', 'True', 'Ready'),
    ]
}


# Successful invocation response. 3 nodes, a1, b1, c1, ready after three
# passes
INV_SEQ_B = {
    '0': [
    ],
    '1': [
        MockNodeStatus('c1', 'True', 'Ready'),
    ],
    '2': [
        MockNodeStatus('c1', 'True', 'Ready'),
    ],
    'final': [
        MockNodeStatus('a1', 'True', 'Ready'),
        MockNodeStatus('b1', 'True', 'Ready'),
        MockNodeStatus('c1', 'True', 'Ready'),
    ]
}

# Successful invocation response. 3 nodes, a1, b1, c1, ready after three
# passes with non-ready nodes appearing along the way
INV_SEQ_C = {
    '0': [
        MockNodeStatus('a1', 'False', 'Not Ready'),
    ],
    '1': [
        MockNodeStatus('a1', 'False', 'Not Ready'),
        MockNodeStatus('b1', 'False', 'Not Ready'),
        MockNodeStatus('c1', 'True', 'Ready'),
    ],
    '2': [
        MockNodeStatus('a1', 'False', 'Not Ready'),
        MockNodeStatus('b1', 'True', 'Ready'),
        MockNodeStatus('c1', 'True', 'Ready'),
    ],
    'final': [
        MockNodeStatus('a1', 'True', 'Ready'),
        MockNodeStatus('b1', 'True', 'Ready'),
        MockNodeStatus('c1', 'True', 'Ready'),
    ]
}

# Malformed invocation response on first try.
# Successful node c1
INV_SEQ_D = {
    'final': [
        MalformedNodeStatus('a1'),
        MalformedNodeStatus(),
        MockNodeStatus('c1', 'True', 'Ready'),
    ],
}


class TestCheckK8sNodeStatus:

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "_get_all_k8s_node_status",
                new=gen_check_node_status(INV_SEQ_A))
    def test_check_node_status_all_success(self):
        """Assert that check_node_status completes successfully

        Simple case - all nodes ready when response has all values
        (set input)
        """
        not_found_nodes = check_node_status(10, 1, set(['a1', 'b1', 'c1']))
        assert not not_found_nodes

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "_get_all_k8s_node_status",
                new=gen_check_node_status(INV_SEQ_A))
    def test_check_node_status_simple_failure(self):
        """Assert that check_node_status completes successfully with failures

        Some nodes successful, but looking for some that never show up.
        (list input)
        """
        not_found_nodes = check_node_status(1, 1, ['a1', 'b1', 'c1', 'z1'])
        assert not_found_nodes == ['z1']

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "_get_all_k8s_node_status",
                new=gen_check_node_status(INV_SEQ_B))
    def test_check_node_status_all_success_4th(self):
        """Assert that check_node_status completes successfully

        All nodes ready on 4th iteration
        """
        not_found_nodes = check_node_status(3, 1, set(['a1', 'b1', 'c1']))
        assert not not_found_nodes

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "_get_all_k8s_node_status",
                new=gen_check_node_status(INV_SEQ_B))
    def test_check_node_status_timeout_before_4th(self):
        """Assert that check_node_status completes successfully with failures

        Some nodes not ready before timeout (before 4th iteration)
        """
        not_found_nodes = check_node_status(2, 1, set(['a1', 'b1', 'c1']))
        assert 'a1' in not_found_nodes
        assert 'b1' in not_found_nodes
        assert 'c1' not in not_found_nodes

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "_get_all_k8s_node_status",
                new=gen_check_node_status(INV_SEQ_C))
    def test_check_node_status_success_changing_status(self):
        """Assert that check_node_status completes successfully

        Nodes go from not ready to ready
        """
        not_found_nodes = check_node_status(30, 1, set(['a1', 'b1', 'c1']))
        assert not not_found_nodes

    def test_check_node_status_no_interest(self):
        """Assert that check_node_status completes successfully

        Returns empty array because nothing was requested to look for.
        """
        not_found_nodes = check_node_status(3, 1, expected_nodes=None)
        assert not not_found_nodes
        not_found_nodes = check_node_status(3, 1, [])
        assert not not_found_nodes
        not_found_nodes = check_node_status(3, 1, set([]))
        assert not not_found_nodes

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "_get_all_k8s_node_status",
                new=gen_check_node_status(INV_SEQ_D))
    def test_check_node_status_malformed(self):
        """Assert that check_node_status completes successfully

        Nodes go from not ready to ready
        """
        not_found_nodes = check_node_status(1, 1, set(['a1', 'b1', 'c1']))
        assert 'a1' in not_found_nodes
        assert 'b1' in not_found_nodes
        assert 'c1' not in not_found_nodes

    def test_check_node_status_error_not_connected_to_k8s(self):
        """Assert that check_node_status completes successfully with failures

        No nodes found because of errors doing lookup.
        """
        not_found_nodes = check_node_status(1, 1, set(['a1', 'b1', 'c1']))
        assert 'a1' in not_found_nodes
        assert 'b1' in not_found_nodes
        assert 'c1' in not_found_nodes

    @mock.patch("shipyard_airflow.plugins.check_k8s_node_status."
                "_get_all_k8s_node_status",
                new=gen_check_node_status(INV_SEQ_A))
    def test_check_node_status_bad_intervals(self):
        """Assert that check_node_status completes successfully

        With bogus timeout and interval values
        """
        not_found_nodes = check_node_status(-1, -1, set(['a1', 'b1', 'c1']))
        assert not not_found_nodes

        not_found_nodes = check_node_status(1, 5, set(['a1', 'b1', 'z1']))
        assert not_found_nodes == ['z1']
