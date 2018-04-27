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
"""Stubs that play the role of a node lookup for testing of DeploymentGroup
related functionality"""


# Lookups for testing different node selectors
_NODE_LABELS = {
    'label1:label1': ['node1', 'node3', 'node5', 'node7', 'node9', 'node11'],
    'label2:label2': ['node2', 'node4', 'node6', 'node8', 'node10', 'node12'],
    'label3:label3': ['node1', 'node2', 'node3', 'node4', 'node5', 'node6'],
    'label4:label4': ['node7', 'node8', 'node9', 'node10', 'node11', 'node12'],
    'compute:true': ['node4', 'node5', 'node7', 'node8', 'node10', 'node11']
}
_NODE_TAGS = {
    'tag1': ['node2', 'node5', 'node8'],
    'tag2': ['node3', 'node6', 'node9'],
    'monitoring': ['node6', 'node9', 'node12']
}
_RACK_NAMES = {
    'rack1': ['node1', 'node2', 'node3'],
    'rack2': ['node4', 'node5', 'node6'],
    'rack3': ['node7', 'node8', 'node9'],
    'rack4': ['node10', 'node11', 'node12'],
}

_ALL_NODES = {'node1', 'node2', 'node3', 'node4', 'node5', 'node6', 'node7',
              'node8', 'node9', 'node10', 'node11', 'node12'}


def node_lookup(selectors):
    """A method that can be used in place of a real node lookup

    Performs a simple intersection of the selector criteria using the
    lookup fields defined above.
    """
    def get_nodes(lookup, keys):
        nodes = []
        for key in keys:
            nodes.extend(lookup[key])
        return set(nodes)
    nodes_full = []
    for selector in selectors:
        nl_list = []
        if selector.all_selector:
            nl_list.append(_ALL_NODES)
        else:
            if selector.node_names:
                nl_list.append(set(selector.node_names))
            if selector.node_labels:
                nl_list.append(get_nodes(_NODE_LABELS,
                                         selector.node_labels))
            if selector.node_tags:
                nl_list.append(get_nodes(_NODE_TAGS, selector.node_tags))
            if selector.rack_names:
                nl_list.append(get_nodes(_RACK_NAMES, selector.rack_names))
        nodes = set.intersection(*nl_list)
        nodes_full.extend(nodes)
    return set(nodes_full)


def crummy_node_lookup(selectors):
    """Returns None"""
    return None


def broken_node_lookup_1(selectors):
    """Doesn't return an iterable """
    return True


def broken_node_lookup_2(selectors):
    """Returns a list of various garbage, not strings"""
    return [{"this": "that"}, 7, "node3"]
