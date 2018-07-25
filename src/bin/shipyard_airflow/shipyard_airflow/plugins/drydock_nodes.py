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
"""Prepare and deploy nodes using Drydock

Uses the deployment strategy named in the deployment-configuration to
progress through preparation and deployment of nodes in a group-based fashion.

In the case of no specified deployment strategy, an "all-at-once" approach is
taken, by which all nodes are deployed together.

Historical Note: This operator replaces the function of drydock_prepare_nodes
and drydock_deploy_nodes operators that existed previously.
"""
import logging
import time

from airflow.exceptions import AirflowException
from airflow.plugins_manager import AirflowPlugin

from shipyard_airflow.common.deployment_group.deployment_group import Stage
from shipyard_airflow.common.deployment_group.deployment_group_manager import \
    DeploymentGroupManager
from shipyard_airflow.common.deployment_group.node_lookup import NodeLookup

try:
    import check_k8s_node_status
    from drydock_base_operator import DrydockBaseOperator
    from drydock_errors import (
        DrydockTaskFailedException,
        DrydockTaskTimeoutException
    )
except ImportError:
    from shipyard_airflow.plugins import check_k8s_node_status
    from shipyard_airflow.plugins.drydock_base_operator import \
        DrydockBaseOperator
    from shipyard_airflow.plugins.drydock_errors import (
        DrydockTaskFailedException,
        DrydockTaskTimeoutException
    )

LOG = logging.getLogger(__name__)


class DrydockNodesOperator(DrydockBaseOperator):
    """Drydock Nodes Operator

    Using a deployment strategy to calculate the deployment sequence,
    deploy a series of baremetal nodes using Drydock.
    """

    def do_execute(self):
        self._setup_configured_values()
        # setup self.strat_name and self.strategy
        self.strategy = {}
        self._setup_deployment_strategy()
        dgm = _get_deployment_group_manager(
            self.strategy['groups'],
            _get_node_lookup(self.drydock_client, self.design_ref)
        )

        _process_deployment_groups(dgm,
                                   self._execute_prepare,
                                   self._execute_deployment)

        # All groups "complete" (as they're going to be). Report summary
        dgm.report_group_summary()
        dgm.report_node_summary()
        if dgm.critical_groups_failed():
            raise AirflowException(
                "One or more deployment groups marked as critical have failed"
            )
        else:
            LOG.info("All critical groups have met their success criteria")
        # TODO (bryan-strassner) it is very possible that many nodes failed
        #     deployment, but all critical groups had enough success to
        #     continue processing. This will be non-obvious to the casual
        #     observer of the workflow. A likely enhancement is to allow
        #     notes be added to the shipyard action associated with this
        #     workflow that would be reported back to the end user doing a
        #     describe of the action. This will require new database structures
        #     to hold the notes, and a means to insert the notes. A shared
        #     functionality in the base ucp operator or a common module would
        #     be a reasonable way to support this.

    def _setup_configured_values(self):
        """Sets self.<name> values from the deployment configuration"""
        # Retrieve query intervals and timeouts
        # Intervals - How often will something be queried for status.
        self.dep_interval = self.dc['physical_provisioner.deploy_interval']
        self.node_st_interval = self.dc['kubernetes.node_status_interval']
        self.prep_interval = self.dc[
            'physical_provisioner.prepare_node_interval'
        ]
        # Timeouts - Time Shipyard waits for completion of a task.
        self.dep_timeout = self.dc['physical_provisioner.deploy_timeout']
        self.node_st_timeout = self.dc['kubernetes.node_status_timeout']
        self.prep_timeout = self.dc[
            'physical_provisioner.prepare_node_timeout'
        ]
        # The time to wait before querying k8s nodes after Drydock deploy nodes
        self.join_wait = self.dc['physical_provisioner.join_wait']

    def _execute_prepare(self, group):
        """Executes the prepare nodes step for the group.

        :param group: the DeploymentGroup to prepare
        Returns a QueryTaskResult object
        """
        LOG.info("Group %s is preparing nodes", group.name)

        self.node_filter = _gen_node_name_filter(group.actionable_nodes)
        return self._execute_task('prepare_nodes',
                                  self.prep_interval,
                                  self.prep_timeout)

    def _execute_deployment(self, group):
        """Execute the deployment of nodes for the group.

        :param group: The DeploymentGroup to deploy
        Returns a QueryTaskResult object
        """
        LOG.info("Group %s is deploying nodes", group.name)

        self.node_filter = _gen_node_name_filter(group.actionable_nodes)
        task_result = self._execute_task('deploy_nodes',
                                         self.dep_interval,
                                         self.dep_timeout)

        if not task_result.successes:
            # if there are no successes from Drydock, there is no need to
            # wait and check on the results from node status.
            LOG.info("There are no nodes indicated as successful from Drydock."
                     " Skipping waiting for Kubernetes node join and "
                     "proceeding to validation")
            return task_result

        # It takes time for the cluster join process to be triggered across
        # all the nodes in the cluster. Hence there is a need to back off
        # and wait before checking the state of the cluster join process.
        LOG.info("Nodes <%s> reported as deployed in MAAS",
                 ", ".join(task_result.successes))
        LOG.info("Waiting for %d seconds before checking node state...",
                 self.join_wait)
        time.sleep(self.join_wait)

        # Check that cluster join process is completed before declaring
        # deploy_node as 'completed'.
        # This should only include nodes that drydock has indicated as
        # successful and has passed the join script to.
        # Anything not ready in the timeout needs to be considered a failure
        not_ready_list = check_k8s_node_status.check_node_status(
            self.node_st_timeout,
            self.node_st_interval,
            expected_nodes=task_result.successes
        )
        for node in not_ready_list:
            # Remove nodes that are not ready from the list of successes, since
            # they did not complete deployment successfully.
            try:
                LOG.info("Node %s failed to join the Kubernetes cluster or was"
                         " not timely enough", node)
                task_result.successes.remove(node)
            except (ValueError, KeyError):
                # This node is not joined, but was not one that we were
                # looking for either.
                LOG.info("%s failed to join Kubernetes, but was not in the "
                         "Drydock results: %s",
                         node,
                         ", ".join(task_result.successes))
        return task_result

    def _execute_task(self, task_name, interval, timeout):
        """Execute the Drydock task requested

        :param task_name: 'prepare_nodes', 'deploy_nodes'
        :param interval: The time between checking status on the task
        :param timeout: The total time allowed for the task

        Wraps the query_task method in the base class, capturing
        AirflowExceptions and summarizing results into a response
        QueryTaskResult object

        Note: It does not matter if the task ultimately succeeds or fails in
        Drydock - the base class will handle all the logging and etc for
        the purposes of troubleshooting. What matters is the node successes.
        Following any result of query_task, this code will re-query the task
        results from Drydock to gather the node successes placing them into
        the successes list in the response object. In the case of a failure to
        get the task results, this workflow must assume that the result is a
        total loss, and pass back no successes
        """
        self.create_task(task_name)
        result = QueryTaskResult(self.drydock_task_id, task_name)

        try:
            self.query_task(interval, timeout)
        except DrydockTaskFailedException:
            # Task failure may be successful enough based on success criteria.
            # This should not halt the overall flow of this workflow step.
            LOG.warn(
                "Task %s has failed. Logs contain details of the failure. "
                "Some nodes may be succesful, processing continues", task_name
            )
        except DrydockTaskTimeoutException:
            # Task timeout may be successful enough based on success criteria.
            # This should not halt the overall flow of this workflow step.
            LOG.warn(
                "Task %s has timed out after %s seconds. Logs contain details "
                "of the failure. Some nodes may be succesful, processing "
                "continues", task_name, timeout
            )
        # Other AirflowExceptions will fail the whole task - let them do this.

        # find successes
        result.successes = self._get_successes_for_task(self.drydock_task_id)
        return result

    def _get_successes_for_task(self, task_id, extend_success=True):
        """Discover the successful nodes based on the current task id.

        :param task_id: The id of the task
        :param extend_successes: determines if this result extends successes
            or simply reports on the task.
        Gets the set of successful nodes by examining the self.drydock_task_id.
        The children are traversed recursively to display each sub-task's
        information.

        Only a reported success at the parent task indicates success of the
        task. Drydock is assumed to roll up overall success to the top level.
        """
        success_nodes = []
        try:
            task_dict = self.get_task_dict(task_id)
            task_status = task_dict.get('status', "Not Specified")
            task_result = task_dict.get('result')
            if task_result is None:
                LOG.warn("Task result is missing for task %s, with status %s."
                         " Neither successes nor further details can be"
                         " extracted from this result",
                         task_id, task_status)
            else:
                if extend_success:
                    try:
                        # successes and failures on the task result drive the
                        # interpretation of success or failure for this
                        # workflow.
                        #  - Any node that is _only_ success for a task is a
                        #    success to us.
                        #  - Any node that is listed as a failure is a failure.
                        # This implies that a node listed as a success and a
                        # failure is a failure. E.g. some subtasks succeeded
                        # and some failed
                        t_successes = task_result.get('successes', [])
                        t_failures = task_result.get('failures', [])
                        actual_successes = set(t_successes) - set(t_failures)
                        # acquire the successes from success nodes
                        success_nodes.extend(actual_successes)
                        LOG.info("Nodes <%s> added as successes for task %s",
                                 ", ".join(success_nodes), task_id)
                    except KeyError:
                        # missing key on the path to getting nodes - don't add
                        LOG.warn(
                            "Missing successes field on result of task %s, "
                            "but a success field was expected. No successes"
                            " can be extracted from this result", task_id
                        )
                        pass
                _report_task_info(task_id, task_result, task_status)

            # for each child, report only the step info, do not add to overall
            # success list.
            for ch_task_id in task_dict.get('subtask_id_list', []):
                success_nodes.extend(
                    self._get_successes_for_task(ch_task_id,
                                                 extend_success=False)
                )
        except Exception:
            # since we are reporting task results, if we can't get the
            # results, do not block the processing.
            LOG.warn("Failed to retrieve a result for task %s. Exception "
                     "follows:", task_id, exc_info=True)

        # deduplicate and return
        return set(success_nodes)

    def _setup_deployment_strategy(self):
        """Determine the deployment strategy

        Uses the specified strategy from the deployment configuration
        or returns a default configuration of 'all-at-once'
        """
        self.strat_name = self.dc['physical_provisioner.deployment_strategy']
        if self.strat_name:
            # if there is a deployment strategy specified, get it and use it
            self.strategy = self.get_unique_doc(
                name=self.strat_name,
                schema="shipyard/DeploymentStrategy/v1"
            )
        else:
            # The default behavior is to deploy all nodes, and fail if
            # any nodes fail to deploy.
            self.strat_name = 'all-at-once (defaulted)'
            self.strategy = _default_deployment_strategy()
        LOG.info("Strategy Name: %s has %s groups",
                 self.strat_name,
                 len(self.strategy.get('groups', [])))


#
# Functions supporting the nodes operator class
#

def _get_node_lookup(drydock_client, design_ref):
    """Return a NodeLookup suitable for the DeploymentGroupManager

    :param drydock_client: the drydock_client object
    :param design_ref: the design_ref for the NodeLookup
    """
    return NodeLookup(drydock_client, design_ref).lookup


def _get_deployment_group_manager(groups_dict_list, node_lookup):
    """Return a DeploymentGroupManager suitable for managing this deployment

    :param groups_dict_list: the list of group dictionaries to use
    :param node_lookup: a NodeLookup object that will be used by this
        DeploymentGroupManager
    """
    return DeploymentGroupManager(groups_dict_list, node_lookup)


def _process_deployment_groups(dgm, prepare_func, deploy_func):
    """Executes the deployment group deployments

    :param dgm: the DeploymentGroupManager object that manages the
        dependency chain of groups
    :param prepare_func: a function that accepts a DeploymentGroup and returns
        a QueryTaskResult with the purpose of preparing nodes
    :param deploy_func: a function that accepts a DeploymentGroup and returns
        a QueryTaskResult with the purpose of deploying nodes
    """
    complete = False
    while not complete:
        # Find the next group to be prepared.  Prepare and deploy it.
        group = dgm.get_next_group(Stage.PREPARED)
        if group is None:
            LOG.info("There are no more groups eligible to process")
            # whether or not really complete, the processing loop is done.
            complete = True
            continue

        LOG.info("*** Deployment Group: %s is being processed ***", group.name)
        if not group.actionable_nodes:
            LOG.info("There were no actionable nodes for group %s. It is "
                     "possible that all nodes: [%s] have previously been "
                     "deployed. Group will be immediately checked "
                     "against its success criteria", group.name,
                     ", ".join(group.full_nodes))

            # In the case of a group having no actionable nodes, since groups
            # prepare -> deploy in direct sequence, we can check against
            # deployment, since all nodes would need to be deployed or have
            # been attempted. Need to follow the state-transition, so
            # PREPARED -> DEPLOYED
            dgm.evaluate_group_succ_criteria(group.name, Stage.PREPARED)
            dgm.evaluate_group_succ_criteria(group.name, Stage.DEPLOYED)
            # success or failure, move on to next group
            continue

        LOG.info("%s has actionable nodes: [%s]", group.name,
                 ", ".join(group.actionable_nodes))
        if len(group.actionable_nodes) < len(group.full_nodes):
            LOG.info("Some nodes are not actionable because they were "
                     "included in a prior group, but will be considered in "
                     "the success critera calculation for this group")

        # Group has actionable nodes.
        # Prepare Nodes for group, store QueryTaskResults
        prep_qtr = prepare_func(group)
        # Mark successes as prepared
        for node_name in prep_qtr.successes:
            dgm.mark_node_prepared(node_name)

        dgm.fail_unsuccessful_nodes(group, prep_qtr.successes)
        should_deploy = dgm.evaluate_group_succ_criteria(group.name,
                                                         Stage.PREPARED)
        if not should_deploy:
            # group has failed, move on to next group. Current group has
            # been marked as failed.
            continue

        # Continue with deployment
        dep_qtr = deploy_func(group)
        # Mark successes as deployed
        for node_name in dep_qtr.successes:
            dgm.mark_node_deployed(node_name)
        dgm.fail_unsuccessful_nodes(group, dep_qtr.successes)
        dgm.evaluate_group_succ_criteria(group.name, Stage.DEPLOYED)


def _report_task_info(task_id, task_result, task_status):
    """Logs information regarding a task.

    :param task_id: id of the task
    :param task_result: The result dictionary of the task
    :param task_status: The status for the task
    """
    # setup fields, or defaults if missing values
    task_failures = task_result.get('failures', [])
    task_successes = task_result.get('successes', [])
    result_details = task_result.get('details', {'messageList': []})
    result_status = task_result.get('status', "No status supplied")
    LOG.info("Task %s with status %s/%s reports successes: [%s] and"
             " failures: [%s]", task_id, task_status, result_status,
             ", ".join(task_successes), ", ".join(task_failures))
    for message_item in result_details['messageList']:
        context_type = message_item.get('context_type', 'N/A')
        context_id = message_item.get('context', 'N/A')
        message = message_item.get('message', "No message text supplied")
        error = message_item.get('error', False)
        timestamp = message_item.get('ts', 'No timestamp supplied')
        LOG.info(" - Task %s for item %s:%s has message: %s [err=%s, at %s]",
                 task_id, context_type, context_id, message, error, timestamp)


def _default_deployment_strategy():
    """The default deployment strategy for 'all-at-once'"""
    return {
        'groups': [
            {
                'name': 'default',
                'critical': True,
                'depends_on': [],
                'selectors': [
                    {
                        'node_names': [],
                        'node_labels': [],
                        'node_tags': [],
                        'rack_names': [],
                    },
                ],
                'success_criteria': {
                    'percent_successful_nodes': 100
                },
            }
        ]
    }


def _gen_node_name_filter(node_names):
    """Generates a drydock compatible node filter using only node names

    :param node_names: the nodes with which to create a filter
    """
    return {
        'filter_set_type': 'union',
        'filter_set': [
            {
                'filter_type': 'union',
                'node_names': node_names
            }
        ]
    }


class QueryTaskResult:
    """Represents a summarized query result from a task"""
    def __init__(self, task_id, task_name):
        self.task_id = task_id
        self.task_name = task_name
        # The succeeded node names
        self.successes = []


class DrydockNodesOperatorPlugin(AirflowPlugin):

    """Creates DrydockPrepareNodesOperator in Airflow."""

    name = 'drydock_nodes_operator'
    operators = [DrydockNodesOperator]
