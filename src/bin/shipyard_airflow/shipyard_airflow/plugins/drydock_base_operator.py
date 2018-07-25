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

from airflow.exceptions import AirflowException
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

    def run_base(self, context):

        # Logs uuid of action performed by the Operator
        LOG.info("DryDock Operator for action %s", self.action_info['id'])

        # Skip workflow if health checks on Drydock failed and continue-on-fail
        # option is turned on
        if self.xcom_puller.get_check_drydock_continue_on_fail():
            LOG.info("Skipping %s as health checks on Drydock have "
                     "failed and continue-on-fail option has been "
                     "turned on", self.__class__.__name__)

            # Set continue processing to False
            self.continue_processing = False

            return

        # Retrieve information of the server that we want to redeploy if user
        # executes the 'redeploy_server' dag
        # Set node filter to be the server that we want to redeploy
        if self.action_info['dag_id'] == 'redeploy_server':
            self.redeploy_server = (
                self.action_info['parameters']['server-name'])

            if self.redeploy_server:
                LOG.info("Server to be redeployed is %s",
                         self.redeploy_server)
                self.node_filter = self.redeploy_server
            else:
                raise AirflowException('%s was unable to retrieve the '
                                       'server to be redeployed.'
                                       % self.__class__.__name__)

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
        LOG.info("Build DryDock Session")
        dd_session = session.DrydockSession(drydock_url.hostname,
                                            port=drydock_url.port,
                                            auth_gen=self._auth_gen)

        # Raise Exception if we are not able to set up the session
        if dd_session:
            LOG.info("Successfully Set Up DryDock Session")
        else:
            raise DrydockClientUseFailureException(
                "Failed to set up Drydock Session!"
            )

        # Use the DrydockSession to build a DrydockClient that can
        # be used to make one or more API calls
        LOG.info("Create DryDock Client")
        self.drydock_client = client.DrydockClient(dd_session)

        # Raise Exception if we are not able to build the client
        if self.drydock_client:
            LOG.info("Successfully Set Up DryDock client")
        else:
            raise DrydockClientUseFailureException(
                "Failed to set up Drydock Client!"
            )

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
            # Dump logs from Drydock pods
            self.get_k8s_logs()

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
                self.get_k8s_logs()
                raise
            except:
                # There can be situations where there are intermittent network
                # issues that prevents us from retrieving the task state. We
                # will want to retry in such situations.
                LOG.warning("Unable to retrieve task state. Retrying...")

            # Raise Time Out Exception
            if task_status == 'running' and i == end_range:
                self.task_failure(False)

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
            self.task_failure(True)

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

    def task_failure(self, _task_failure):
        # Dump logs from Drydock pods
        self.get_k8s_logs()

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

        # Raise Exception to terminate workflow
        if _task_failure:
            raise DrydockTaskFailedException(
                "Failed to Execute/Complete Task!"
            )
        else:
            raise DrydockTaskTimeoutException(
                "Task Execution Timed Out!"
            )

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


class DrydockBaseOperatorPlugin(AirflowPlugin):

    """Creates DrydockBaseOperator in Airflow."""

    name = 'drydock_base_operator_plugin'
    operators = [DrydockBaseOperator]
