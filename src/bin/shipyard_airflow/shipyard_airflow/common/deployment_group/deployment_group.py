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
"""Deployment group module

Encapsulates classes and functions that provide core deployment group
functionality used during baremetal provisioning.
"""
from enum import Enum
import logging
import operator

from .errors import DeploymentGroupLabelFormatError
from .errors import DeploymentGroupStageError
from .errors import InvalidDeploymentGroupError
from .errors import InvalidDeploymentGroupNodeLookupError

LOG = logging.getLogger(__name__)


def check_label_format(label_string):
    """Validates that a label_string is in key:value format.

    Raises DeploymentGroupLabelFormatError if the value is not compliant.
    """
    split = label_string.split(":")
    if not len(split) == 2:
        raise DeploymentGroupLabelFormatError(
            "Label {} is formatted incorrectly. One : (colon) character is "
            "required, and the label must be in key:value format".format(
                label_string)
        )
    for v in split:
        if v.strip() == "":
            raise DeploymentGroupLabelFormatError(
                "Label {} is formatted incorrectly. The values on either side "
                "of the colon character must not be empty.".format(
                    label_string)
            )


class Stage(Enum):
    """Valid values for baremetal node and deployment group stages of
    deployment
    """
    # A node that has not yet started deployment. The default.
    NOT_STARTED = 'NOT_STARTED'
    # A node that has finished the prepare_node stage successfully
    PREPARED = 'PREPARED'
    # A node that has finished the deploy_node stage successfully
    DEPLOYED = 'DEPLOYED'
    # A node that has failed to complete in any step.
    FAILED = 'FAILED'

    @classmethod
    def is_complete(cls, stage):
        return stage in [cls.DEPLOYED, cls.FAILED]

    @classmethod
    def previous_stage(cls, stage):
        """The valid states before the supplied state"""
        if stage == cls.NOT_STARTED:
            return []
        if stage == cls.PREPARED:
            return [cls.NOT_STARTED]
        if stage == cls.DEPLOYED:
            return [cls.PREPARED]
        if stage == cls.FAILED:
            return [cls.NOT_STARTED, cls.PREPARED]
        else:
            raise DeploymentGroupStageError("{} is not a valid stage".format(
                                            str(stage)))


class GroupNodeSelector:
    """GroupNodeSelector object

    :param selector_dict: dictionary representing the possible selector values

    Encapsulates the criteria defining the selector for a deployment group.
    Example selector_dict::

        {
            'node_names': [],
            'node_labels': [],
            'node_tags': ['control'],
            'rack_names': ['rack03'],
        }
    """
    def __init__(self, selector_dict):
        self.node_names = selector_dict.get('node_names', [])
        self.node_labels = selector_dict.get('node_labels', [])
        self.node_tags = selector_dict.get('node_tags', [])
        self.rack_names = selector_dict.get('rack_names', [])

        for label in self.node_labels:
            check_label_format(label)

        # A selector is an "all_selector" if there are no criteria specified.
        self.all_selector = not any([self.node_names, self.node_labels,
                                     self.node_tags, self.rack_names])
        if self.all_selector:
            LOG.debug("Selector values select all available nodes")

    def get_node_labels_as_dict(self):
        return {label.split(':')[0].strip(): label.split(':')[1].strip()
                for label in self.node_labels}


class SuccessCriteria:
    """Defines the success criteria for a deployment group

    :param criteria: a dictionary containing up to 3 fields in
        percent_successful_nodes, minimum_successful_nodes,
        maximum_failed_nodes

    If no criteria are specified, all results are considered a success
    """
    def __init__(self, criteria):
        if not criteria:
            self._always_succeed = True
            return

        self._always_succeed = False
        # set the criteria or let them be None
        self.pct_succ_nodes = criteria.get('percent_successful_nodes')
        self.min_succ_nodes = criteria.get('minimum_successful_nodes')
        self.max_failed_nodes = criteria.get('maximum_failed_nodes')

    def get_failed(self, succ_list, all_nodes_list):
        """Determine which criteria have failed.

        :param succ_list: A list of names of nodes that have successfully
            completed a stage
        :param all_nodes_list: A list of all node names that are to be
            evaluated against.

        Using the provided list of successful nodes, and the list of all
        nodes, check which of the success criteria have failed to have been
        met.
        """
        failures = []

        # If no criteria, or list of all nodes is empty, return empty list
        if self._always_succeed or len(all_nodes_list) == 0:
            return failures

        succ_set = set(succ_list)
        all_set = set(all_nodes_list)

        all_size = len(all_set)
        succ_size = len(succ_set.intersection(all_set))
        fail_size = len(all_set.difference(succ_set))
        actual_pct_succ = succ_size / all_size * 100

        failures.extend(self._check("percent_successful_nodes",
                                    actual_pct_succ, operator.ge,
                                    self.pct_succ_nodes))
        failures.extend(self._check("minimum_successful_nodes", succ_size,
                                    operator.ge, self.min_succ_nodes))

        failures.extend(self._check("maximum_failed_nodes", fail_size,
                                    operator.le, self.max_failed_nodes))
        return failures

    def _check(self, name, actual, op, needed):
        """Evaluates a single criteria

        :param name: name of the check
        :param actual: the result that was achieved (LHS)
        :param op: operator used for comparison
        :param needed: the threshold of success (RHS). If this parameter
            is None, the criteria is ignored as "successful" because it
            was not set as a needed criteria

        Returns a list containing the failure dictionary if the comparison
        fails or and empty list if check is successful.
        """
        if needed is None:
            LOG.info(" - %s criteria not specified, not evaluated", name)
            return []

        if op(actual, needed):
            LOG.info(" - %s succeeded, %s %s %s", name, actual, op.__name__,
                     needed)
            return []
        else:
            fail = {"criteria": name, "needed": needed, "actual": actual}
            LOG.info(" - %s failed, %s %s %s", name, actual, op.__name__,
                     needed)
            return [fail]


class DeploymentGroup:
    """DeploymentGroup object representing a deployment group

    :param group_dict: dictionary representing a group
    :param node_lookup: an injected function that will perform node lookup for
        a group. Function must accept an iterable of GroupNodeSelector and
        return a string iterable of node names (or empty iterable if there are
        no node names)

    Example group_dict::

        {
            'name': 'control-nodes',
            'critical': True,
            'depends_on': ['ntp-node'],
            'selectors': [
                {
                    'node_names': [],
                    'node_labels': [],
                    'node_tags': ['control'],
                    'rack_names': ['rack03'],
                },
            ],
            'success_criteria': {
                'percent_successful_nodes': 90,
                'minimum_successful_nodes': 3,
                'maximum_failed_nodes': 1,
            },
        }
    """
    def __init__(self, group_dict, node_lookup):
        # store the original dictionary
        self._group_dict = group_dict

        # fields required by schema
        self._check_required_fields()

        self.critical = group_dict['critical']
        self.depends_on = group_dict['depends_on']
        self.name = group_dict['name']

        self.selectors = []
        for selector_dict in group_dict['selectors']:
            self.selectors.append(GroupNodeSelector(selector_dict))
        if not self.selectors:
            # no selectors means add an "all" selector
            self.selectors.append(GroupNodeSelector({}))

        self.success_criteria = SuccessCriteria(
            group_dict.get('success_criteria', {})
        )

        # all groups start as NOT_STARTED
        self.__stage = None
        self.stage = Stage.NOT_STARTED

        # node_lookup function for use with this deployment group
        # lookup the full list of nodes for this group's selectors
        self.node_lookup = node_lookup
        self.full_nodes = self._calculate_all_nodes()

        # actionable_nodes is set up based on multi-group interaction.
        # Only declaring the field here. Used for deduplicaiton.
        self.actionable_nodes = []

    @property
    def stage(self):
        return self.__stage

    @stage.setter
    def stage(self, stage):
        valid_prior = Stage.previous_stage(stage)
        pre_change_stage = self.__stage
        if self.__stage == stage:
            return
        elif self.__stage is None and not valid_prior:
            self.__stage = stage
        elif self.__stage in valid_prior:
            self.__stage = stage
        else:
            raise DeploymentGroupStageError(
                "{} is not a valid stage for a group in stage {}".format(
                    stage, self.__stage
                ))
        LOG.info("Setting group %s with %s -> %s",
                 self.name,
                 pre_change_stage,
                 stage)

    def _check_required_fields(self):
        """Checks for required input fields and errors if any are missing"""
        for attr in ['critical', 'depends_on', 'name', 'selectors']:
            try:
                value = self._group_dict[attr]
                LOG.debug("Attribute %s has value %s", attr, str(value))
            except KeyError:
                raise InvalidDeploymentGroupError(
                    "Attribute '{}' is required as input to create a "
                    "DeploymentGroup".format(attr))

    def _calculate_all_nodes(self):
        """Invoke the node_lookup to retrieve nodes

        After construction of the DeploymentGroup, this method is generally
        not useful as the results are stored in self.full_nodes
        """
        LOG.debug("Beginning lookup of nodes for group %s", self.name)
        nodes = self.node_lookup(self.selectors)
        if nodes is None:
            nodes = []
        try:
            node_list = list(nodes)
        except TypeError:
            raise InvalidDeploymentGroupNodeLookupError(
                "The node lookup function supplied to the DeploymentGroup "
                "is not an iterable"
            )
        if not all(isinstance(node, str) for node in node_list):
            raise InvalidDeploymentGroupNodeLookupError(
                "The node lookup function supplied to the DeploymentGroup "
                "is not all strings"
            )
        LOG.info("Group %s selectors have resolved to nodes: %s",
                 self.name, ", ".join(node_list))
        return node_list

    def get_failed_success_criteria(self, success_node_list):
        """Check the success criteria for this group.

        :param success_node_list: list of nodes that are deemed successful
            to be compared to the success criteria

        Using the list of all nodes, and the provided success_node_list,
        use the SuccessCriteria for this group to see if that list of
        successes meets the criteria.
        Note that this is not checking for any particular stage of deployment,
        simply the comparison of the total list of nodes to the provided list.
        Returns a list of failures. An empty list indicates successful
        comparison with all criteria.

        A good pattern for use of this method is to provide a list of all
        nodes being deployed across all groups that are successful for a
        given stage of deployment (e.g. all prepared, all deployed).
        Calculations are done using set comparisons, so nodes that are not
        important for this group will be ignored. It is important *not* to
        provide only a list of nodes that were recently acted upon as part of
        this group, as deduplication from overlapping groups may cause the
        calculations to be skewed and report false failures.
        """
        LOG.info('Assessing success criteria for group %s', self.name)
        sc = self.success_criteria.get_failed(success_node_list,
                                              self.full_nodes)
        if sc:
            LOG.info('Group %s failed success criteria', self.name)
        else:
            LOG.info('Group %s success criteria passed', self.name)
        return sc
