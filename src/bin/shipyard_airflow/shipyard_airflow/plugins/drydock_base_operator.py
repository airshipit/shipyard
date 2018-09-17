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
import copy
import pprint
import logging
import time
from urllib.parse import urlparse

from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

import drydock_provisioner.drydock_client.client as client
import drydock_provisioner.drydock_client.session as session
from drydock_provisioner import error as errors

try:
    from drydock_errors import (
        DrydockClientUseFailureException,
        DrydockTaskFailedException,
        DrydockTaskNotCreatedException,
        DrydockTaskTimeoutException
    )
    import service_endpoint
    from service_token import shipyard_service_token
    from ucp_base_operator import UcpBaseOperator

except ImportError:
    from shipyard_airflow.plugins.drydock_errors import (
        DrydockClientUseFailureException,
        DrydockTaskFailedException,
        DrydockTaskNotCreatedException,
        DrydockTaskTimeoutException
    )
    from shipyard_airflow.plugins import service_endpoint
    from shipyard_airflow.plugins.service_token import shipyard_service_token
    from shipyard_airflow.plugins.ucp_base_operator import UcpBaseOperator

LOG = logging.getLogger(__name__)


class DrydockBaseOperator(UcpBaseOperator):
    """Drydock Base Operator

    All drydock related workflow operators will use the drydock
    base operator as the parent and inherit attributes and methods
    from this class
    """

    @apply_defaults
    def __init__(self,
                 drydock_client=None,
                 drydock_task_id=None,
                 node_filter=None,
                 redeploy_server=None,
                 svc_session=None,
                 svc_token=None,
                 *args, **kwargs):
        """Initialization of DrydockBaseOperator object.

        :param drydockclient: An instance of drydock client
        :param drydock_task_id: Drydock Task ID
        :param node_filter: A filter for narrowing the scope of the task.
                            Valid fields are 'node_names', 'rack_names',
                            'node_tags'. Note that node filter is turned
                            off by default, i.e. all nodes will be deployed.
        :param redeploy_server: Server to be redeployed
        :param svc_session: Keystone Session
        :param svc_token: Keystone Token

        The Drydock operator assumes that prior steps have set xcoms for
        the action and the deployment configuration

        """
        super(DrydockBaseOperator,
              self).__init__(
                  pod_selector_pattern=[{'pod_pattern': 'drydock-api',
                                         'container': 'drydock-api'}],
                  *args, **kwargs)
        self.drydock_client = drydock_client
        self.drydock_task_id = drydock_task_id
        self.node_filter = node_filter
        self.redeploy_server = redeploy_server
        self.svc_session = svc_session
        self.svc_token = svc_token
        self.target_nodes = None

    def run_base(self, context):
        """Base setup/processing for Drydock operators

        :param context: the context supplied by the dag_run in Airflow
        """
        LOG.debug("Drydock Operator for action %s", self.action_id)
        # if continue processing is false, don't bother setting up things.
        if self._continue_processing_flag():
            self._setup_drydock_client()

    def _continue_processing_flag(self):
        """Checks if this processing should continue or not

        Skip workflow if health checks on Drydock failed and continue-on-fail
        option is turned on.
        Returns the self.continue_processing value.
        """
        if self.xcom_puller.get_check_drydock_continue_on_fail():
            LOG.info("Skipping %s as health checks on Drydock have "
                     "failed and continue-on-fail option has been "
                     "turned on", self.__class__.__name__)
            # Set continue processing to False
            self.continue_processing = False

        return self.continue_processing

    def _setup_drydock_client(self):
        """Setup the drydock client for use by this operator"""
        # Retrieve Endpoint Information
        self.drydock_svc_endpoint = self.endpoints.endpoint_by_name(
            service_endpoint.DRYDOCK
        )

        LOG.info("Drydock endpoint is %s", self.drydock_svc_endpoint)

        # Parse DryDock Service Endpoint
        drydock_url = urlparse(self.drydock_svc_endpoint)

        # Build a DrydockSession with credentials and target host
        # information.
        # The DrydockSession will care for TCP connection pooling
        # and header management
        dd_session = session.DrydockSession(drydock_url.hostname,
                                            port=drydock_url.port,
                                            auth_gen=self._auth_gen)

        # Raise Exception if we are not able to set up the session
        if not dd_session:
            raise DrydockClientUseFailureException(
                "Failed to set up Drydock Session!"
            )

        # Use the DrydockSession to build a DrydockClient that can
        # be used to make one or more API calls
        self.drydock_client = client.DrydockClient(dd_session)
        # Raise Exception if we are not able to build the client
        if not self.drydock_client:
            raise DrydockClientUseFailureException(
                "Failed to set up Drydock Client!"
            )
        LOG.info("Drydock Session and Client etablished.")

    @shipyard_service_token
    def _auth_gen(self):
        # Generator method for the Drydock Session to use to get the
        # auth headers necessary
        return [('X-Auth-Token', self.svc_token)]

    def create_task(self, task_action):

        # Initialize Variables
        create_task_response = {}

        # Node Filter
        LOG.info("Nodes Filter List: %s", self.node_filter)

        try:
            # Create Task
            create_task_response = self.drydock_client.create_task(
                design_ref=self.design_ref,
                task_action=task_action,
                node_filter=self.node_filter)

        except errors.ClientError as client_error:
            raise DrydockClientUseFailureException(client_error)

        # Retrieve Task ID
        self.drydock_task_id = create_task_response['task_id']
        LOG.info('Drydock %s task ID is %s',
                 task_action, self.drydock_task_id)

        # Raise Exception if we are not able to get the task_id from
        # Drydock
        if self.drydock_task_id:
            return self.drydock_task_id
        else:
            raise DrydockTaskNotCreatedException("Unable to create task!")

    def query_task(self, interval, time_out):

        # Calculate number of times to execute the 'for' loop
        # Convert 'time_out' and 'interval' from string into integer
        # The result from the division will be a floating number which
        # We will round off to nearest whole number
        end_range = round(int(time_out) / int(interval))

        LOG.info('Task ID is %s', self.drydock_task_id)
        task_result = None

        # Query task status
        for i in range(0, end_range + 1):
            task_status = None

            try:
                # Retrieve current task state
                task_state = self.get_task_dict(task_id=self.drydock_task_id)

                task_status = task_state['status']
                task_result = task_state['result']['status']

                LOG.info("Current status of task id %s is %s",
                         self.drydock_task_id, task_status)
            except DrydockClientUseFailureException:
                raise
            except:
                # There can be situations where there are intermittent network
                # issues that prevents us from retrieving the task state. We
                # will want to retry in such situations.
                LOG.warning("Unable to retrieve task state. Retrying...")

            # Raise Time Out Exception
            if task_status == 'running' and i == end_range:
                # TODO(bryan-strassner) If Shipyard has timed out waiting for
                #     this task to complete, and Drydock has provided a means
                #     to cancel a task, that cancellation should be done here.
                raise DrydockTaskTimeoutException("Task Execution Timed Out!")

            # Exit 'for' loop if the task is in 'complete' or 'terminated'
            # state
            if task_status in ['complete', 'terminated']:
                LOG.info('Task result is %s', task_result)
                break
            else:
                time.sleep(int(interval))

        # Get final task result
        if task_result == 'success':
            LOG.info('Task id %s has been successfully completed',
                     self.drydock_task_id)
        else:
            raise DrydockTaskFailedException(
                "Failed to Execute/Complete Task!")

    def get_task_dict(self, task_id):
        """Retrieve task output in its raw dictionary format

        :param task_id: The id of the task to retrieve
        Raises DrydockClientUseFailureException if the client raises an
        exception
        See:
        http://att-comdev-drydock.readthedocs.io/en/latest/task.html#task-status-schema
        """
        try:
            return self.drydock_client.get_task(task_id=task_id)
        except errors.ClientError as client_error:
            raise DrydockClientUseFailureException(client_error)

    def fetch_failure_details(self):
        LOG.info('Retrieving all tasks records from Drydock...')

        try:
            # Get all tasks records
            all_tasks = self.drydock_client.get_tasks()

            # Create a dictionary of tasks records with 'task_id' as key
            self.all_task_ids = {t['task_id']: t for t in all_tasks}

        except errors.ClientError as client_error:
            raise DrydockClientUseFailureException(client_error)

        # Retrieve the failed parent task and assign it to list
        failed_parent_task = (
            [x for x in all_tasks if x['task_id'] == self.drydock_task_id])

        # Print detailed information of failed parent task in json output
        # Since there is only 1 failed parent task, we will print index 0
        # of the list
        if failed_parent_task:
            LOG.error("%s task has either failed or timed out",
                      failed_parent_task[0]['action'])

            LOG.error(pprint.pprint(failed_parent_task[0]))

            # Get the list of subtasks belonging to the failed parent task
            parent_subtask_id_list = failed_parent_task[0]['subtask_id_list']

            # Check for failed subtasks
            self.check_subtask_failure(parent_subtask_id_list)
        else:
            LOG.info("No failed parent task found for task_id %s",
                     self.drydock_task_id)

    def check_subtask_failure(self, subtask_id_list):

        LOG.info("Printing information of failed sub-tasks...")

        while subtask_id_list:

            # Copies the current list (a layer)
            children_subtask_id_list = copy.copy(subtask_id_list)

            # Reset subtask_id_list for each layer
            # The last layer will be an empty list
            subtask_id_list = []

            # Print detailed information of failed step(s) under each
            # subtask. This will help to provide additional information
            # for troubleshooting purpose.
            for subtask_id in children_subtask_id_list:

                LOG.info("Retrieving details of subtask %s...", subtask_id)

                # Retrieve task information
                task = self.all_task_ids.get(subtask_id)

                if task:
                    # Print subtask action and state
                    LOG.info("%s subtask is in %s state",
                             task['action'],
                             task['result']['status'])

                    # Check for subtasks and extend the list
                    subtask_id_list.extend(task['subtask_id_list'])

                    # Check if error count is greater than 0
                    if task['result']['details']['errorCount'] > 0:

                        # Get message list
                        message_list = (
                            task['result']['details']['messageList'] or [])

                        # Print information of failed steps
                        for message in message_list:
                            is_error = message['error'] is True

                            if is_error:
                                LOG.error(pprint.pprint(message))

                    else:
                        LOG.info("No failed step detected for subtask %s",
                                 subtask_id)

                else:
                    raise DrydockClientUseFailureException(
                        "Unable to retrieve subtask info!"
                    )

    def get_nodes(self):
        """
        Get the list of all the build data record for all nodes(hostname)
        in raw dictionary format.

        Raises DrydockClientUseFailureException if the client raises an
        exception
        See:
        https://att-comdev-drydock.readthedocs.io/en/latest/API.html
        """
        try:
            return self.drydock_client.get_nodes()
        except errors.ClientError as client_error:
            LOG.error("Drydock client failed to get nodes from Drydock.")
            raise DrydockClientUseFailureException(client_error)

    def get_successes_for_task(self, task_id, extend_success=True):
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
                    self.get_successes_for_task(ch_task_id,
                                                extend_success=False)
                )
        except Exception:
            # since we are reporting task results, if we can't get the
            # results, do not block the processing.
            LOG.warn("Failed to retrieve a result for task %s. Exception "
                     "follows:", task_id, exc_info=True)

        # deduplicate and return
        return set(success_nodes)


def gen_node_name_filter(node_names):
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


class DrydockBaseOperatorPlugin(AirflowPlugin):

    """Creates DrydockBaseOperator in Airflow."""

    name = 'drydock_base_operator_plugin'
    operators = [DrydockBaseOperator]
