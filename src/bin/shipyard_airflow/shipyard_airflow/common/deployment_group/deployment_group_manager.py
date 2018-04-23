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
"""Deployment group manager module

Encapsulates classes and functions related to the management and use of
deployment groups used during baremetal provisioning.
"""
import logging

import networkx as nx

from .deployment_group import DeploymentGroup
from .deployment_group import Stage
from .errors import DeploymentGroupCycleError
from .errors import DeploymentGroupStageError
from .errors import UnknownDeploymentGroupError
from .errors import UnknownNodeError

LOG = logging.getLogger(__name__)


class DeploymentGroupManager:
    """Manager object to control ordering and cross-group interactions

    :param group_dict_list: list of group entries translated from a
        DeploymentStrategy document.
    :param node_lookup: function to lookup nodes based on group selectors
    """

    def __init__(self, group_dict_list, node_lookup):
        LOG.debug("Initializing DeploymentGroupManager")

        # the raw input
        self._group_dict_list = group_dict_list

        # A dictionary of all groups by group name. E.g.:
        # {
        #   'group-1': DeploymentGroup(...),
        # }
        self._all_groups = {}
        for group_dict in group_dict_list:
            group = DeploymentGroup(group_dict, node_lookup)
            self._all_groups[group.name] = group

        self._group_graph = _generate_group_graph(
            self._all_groups.values()
        )
        self._group_order = list(nx.topological_sort(self._group_graph))

        # Setup nodes.
        # self.all_nodes is a dictionary of all nodes by node name,
        # representing each node's status of deployment. E.g.:
        # { 'node-01' : Stage.NOT_STARTED}
        #
        # each group is also updated with group.actionable_nodes based on group
        # ordering (deduplication)
        self._all_nodes = {}
        self._calculate_nodes()

    def get_next_group(self, stage):
        """Get the next eligible group name to use for the provided stage

        Finds the next group that has as status eligible for the stage
        provided.
        Returns None if there are no groups ready for the stage
        """
        prev_stage = Stage.previous_stage(stage)
        for group in self._group_order:
            if self._all_groups[group].stage in prev_stage:
                return self._all_groups[group]
        return None

    #
    # Methods that support setup of the nodes in groups
    #

    def _calculate_nodes(self):
        """Calculate the mapping of all compute nodes

        Uses self.group_order, self.all_groups
        """
        for name in self._group_order:
            group = self._all_groups[name]
            known_nodes = set(self._all_nodes.keys())
            _update_group_actionable_nodes(group, known_nodes)
            for node in group.full_nodes:
                self._all_nodes[node] = Stage.NOT_STARTED

    #
    # Methods for managing marking the stage of processing for a group
    #

    def mark_group_failed(self, group_name):
        """Sets status for a group and all successors(dependents) to failed

        :param group_name: The name of the group to fail
        """
        group = self._find_group(group_name)
        group.stage = Stage.FAILED
        successors = list(self._group_graph.successors(group_name))
        if successors:
            LOG.info("Group %s (now FAILED) has dependent groups %s",
                     group_name, ", ".join(successors))
            for name in successors:
                self.mark_group_failed(name)

    def mark_group_prepared(self, group_name):
        """Sets a group to the Stage.PREPARED stage"""
        group = self._find_group(group_name)
        group.stage = Stage.PREPARED

    def mark_group_deployed(self, group_name):
        """Sets a group to the Stage.DEPLOYED stage"""
        group = self._find_group(group_name)
        group.stage = Stage.DEPLOYED

    def _find_group(self, group_name):
        """Wrapper for accessing groups from self.all_groups"""
        group = self._all_groups.get(group_name)
        if group is None:
            raise UnknownDeploymentGroupError(
                "Group name {} does not refer to a known group".format(
                    group_name)
            )
        return group

    def get_group_failures_for_stage(self, group_name, stage):
        """Check if the nodes of a group cause the group to fail

        Returns the list of failed success criteria, or [] if the group is
        successful
        This is only for checking transitions to PREPARED and DEPLOYED. The
        valid stages for input to this method are Stage.PREPARED and
        Stage.DEPLOYED.
        Note that nodes that are DEPLOYED count as PREPARED, but not
        the other way around.
        """
        if stage not in [Stage.DEPLOYED, Stage.PREPARED]:
            raise DeploymentGroupStageError(
                "The stage {} is not valid for checking group"
                " failures.".format(stage))
        success_nodes = set()
        # deployed nodes count as success for prepared and deployed
        success_nodes.update(self.get_nodes(Stage.DEPLOYED))
        if stage == Stage.PREPARED:
            success_nodes.update(self.get_nodes(Stage.PREPARED))
        group = self._find_group(group_name)
        return group.get_failed_success_criteria(success_nodes)

    #
    # Methods for handling nodes
    #

    def mark_node_deployed(self, node_name):
        """Mark a node as deployed"""
        self._set_node_stage(node_name, Stage.DEPLOYED)

    def mark_node_prepared(self, node_name):
        """Mark a node as prepared"""
        self._set_node_stage(node_name, Stage.PREPARED)

    def mark_node_failed(self, node_name):
        """Mark a node as failed"""
        self._set_node_stage(node_name, Stage.FAILED)

    def _set_node_stage(self, node_name, stage):
        """Find and set a node's stage to the specified stage"""
        if node_name in self._all_nodes:
            self._all_nodes[node_name] = stage
        else:
            raise UnknownNodeError("The specified node {} does not"
                                   " exist in this manager".format(node_name))

    def get_nodes(self, stage=None):
        """Get a list of nodes that have the specified status"""
        if stage is None:
            return [name for name in self._all_nodes]

        return [name for name, n_stage
                in self._all_nodes.items()
                if n_stage == stage]


def _update_group_actionable_nodes(group, known_nodes):
    """Updates a group's actionable nodes

    Acitonable nodes is the group's (full_nodes - known_nodes)
    """
    LOG.debug("Known nodes before processing group %s is %s",
              group.name,
              ", ".join(known_nodes))

    group_nodes = set(group.full_nodes)
    group.actionable_nodes = group_nodes.difference(known_nodes)
    LOG.debug("Group %s set actionable_nodes to %s. "
              "Full node list for this group is %s",
              group.name,
              ", ".join(group.actionable_nodes),
              ", ".join(group.full_nodes))


def _generate_group_graph(groups):
    """Create the directed graph of groups

    :param groups: An iterable of DeploymentGroup objects
    returns a directed graph of group names
    """
    LOG.debug("Generating directed graph of groups based on dependencies")
    graph = nx.DiGraph()
    # Add all groups as graph nodes. It is not strictly necessary to do two
    # loops here, but n is small and for obviousness.
    for group in groups:
        graph.add_node(group.name)

    # Add all edges
    for group in groups:
        if group.depends_on:
            for parent in group.depends_on:
                LOG.debug("%s has parent %s", group.name, parent)
                graph.add_edge(parent, group.name)
        else:
            LOG.debug("%s is not dependent upon any other groups")

    _detect_cycles(graph)
    return graph


def _detect_cycles(graph):
    """Detect if there are cycles between the groups

    Raise a DeploymentGroupCycleError if there are any circular
    dependencies
    """
    LOG.debug("Detecting cycles in graph")
    circ_deps = []
    try:
        circ_deps = list(nx.find_cycle(graph))
    except nx.NetworkXNoCycle:
        LOG.info('There are no cycles detected in the graph')
        pass

    if circ_deps:
        involved_nodes = set()
        # a value in this list is like: ('group1', 'group2')
        for dep in circ_deps:
            involved_nodes.update(dep)
        raise DeploymentGroupCycleError(
            "The following are involved in a circular dependency:"
            " %s", ", ".join(involved_nodes)
        )
