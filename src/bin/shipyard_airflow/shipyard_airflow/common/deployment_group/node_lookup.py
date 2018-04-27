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
#
"""A node_lookup class with a lookup method that can be used to access Drydock
to retrieve nodes based on a list of GroupNodeSelector objects
"""
import logging

from .deployment_group import GroupNodeSelector
from .errors import (
    InvalidDeploymentGroupNodeLookupError
)

LOG = logging.getLogger(__name__)


class NodeLookup:
    """Provides NodeLookup functionality

    :param drydock_client: a Drydock Client (Api Client from Drydock)
    :param design_ref: the design ref that will be used to perform a lookup
    """
    def __init__(self, drydock_client, design_ref):
        # Empty dictionary or none for design ref will not work.
        if not design_ref:
            raise InvalidDeploymentGroupNodeLookupError(
                "An incomplete design ref was supplied to the NodeLookup: "
                " {}".format(str(design_ref))
            )
        if drydock_client is None:
            raise TypeError('Drydock client is required.')
        self.design_ref = design_ref
        self.drydock_client = drydock_client

    def lookup(self, selectors):
        """Lookup method

        :param selectors: list of GroupNodeSelector objects used to construct
            a request against Drydock to get a list of nodes
        """
        sel_list = _validate_selectors(selectors)
        node_filter = _generate_node_filter(sel_list)
        return _get_nodes_for_filter(self.drydock_client,
                                     self.design_ref,
                                     node_filter)


def _validate_selectors(selectors):
    """Validate that the selectors are in a valid format and return a list"""
    try:
        sel_list = list(selectors)
    except TypeError:
        raise InvalidDeploymentGroupNodeLookupError(
            "The node lookup function requires an iterable of "
            "GroupNodeSelectors as input"
        )
    if not (all(isinstance(sel, GroupNodeSelector) for sel in sel_list)):
        raise InvalidDeploymentGroupNodeLookupError(
            "The node lookup function requires all input elements in the "
            "selectors be GroupNodeSelectors"
        )
    return sel_list


def _generate_node_filter(selectors):
    """Create a Drydock node_filter based on the input selectors"""
    node_filter = {}
    node_filter['filter_set_type'] = 'union'
    node_filter['filter_set'] = []
    for sel in selectors:
        if sel.all_selector:
            # Drydock regards the lack of a selector as being 'all',
            # and an intersection of all with other criteria is the same as
            # just the other criteria.
            continue
        filter_ = {'filter_type': 'intersection'}
        filter_['node_names'] = sel.node_names
        filter_['node_tags'] = sel.node_tags
        filter_['node_labels'] = sel.get_node_labels_as_dict()
        filter_['rack_names'] = sel.rack_names
        node_filter['filter_set'].append(filter_)

    if not node_filter['filter_set']:
        # if there have been no filters added to the filter set, we want
        # an empty filter object (all) instead of having one that has no
        # criteria (none)
        node_filter = None
    return node_filter


def _get_nodes_for_filter(client, design_ref, node_filter):
    return set(client.get_nodes_for_filter(
        design_ref=design_ref,
        node_filter=node_filter
    ))
