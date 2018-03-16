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

import logging
import os
import time
from urllib.parse import urlparse

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

import drydock_provisioner.drydock_client.client as client
import drydock_provisioner.drydock_client.session as session
from drydock_provisioner import error as errors
from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token
from xcom_puller import XcomPuller


class DrydockBaseOperator(BaseOperator):

    """Drydock Base Operator

    All drydock related workflow operators will use the drydock
    base operator as the parent and inherit attributes and methods
    from this class

    """

    @apply_defaults
    def __init__(self,
                 deckhand_design_ref=None,
                 deckhand_svc_type='deckhand',
                 drydock_client=None,
                 drydock_svc_endpoint=None,
                 drydock_svc_type='physicalprovisioner',
                 drydock_task_id=None,
                 main_dag_name=None,
                 node_filter=None,
                 redeploy_server=None,
                 shipyard_conf=None,
                 sub_dag_name=None,
                 svc_session=None,
                 svc_token=None,
                 xcom_push=True,
                 *args, **kwargs):
        """Initialization of DrydockBaseOperator object.

        :param deckhand_design_ref: A URI reference to the design documents
        :param deckhand_svc_type: Deckhand Service Type
        :param drydockclient: An instance of drydock client
        :param drydock_svc_endpoint: Drydock Service Endpoint
        :param drydock_svc_type: Drydock Service Type
        :param drydock_task_id: Drydock Task ID
        :param main_dag_name: Parent Dag
        :param node_filter: A filter for narrowing the scope of the task.
                            Valid fields are 'node_names', 'rack_names',
                            'node_tags'. Note that node filter is turned
                            off by default, i.e. all nodes will be deployed.
        :param redeploy_server: Server to be redeployed
        :param shipyard_conf: Location of shipyard.conf
        :param sub_dag_name: Child Dag
        :param svc_session: Keystone Session
        :param svc_token: Keystone Token
        :param xcom_push: xcom usage

        The Drydock operator assumes that prior steps have set xcoms for
        the action and the deployment configuration

        """

        super(DrydockBaseOperator, self).__init__(*args, **kwargs)
        self.deckhand_design_ref = deckhand_design_ref
        self.deckhand_svc_type = deckhand_svc_type
        self.drydock_client = drydock_client
        self.drydock_svc_endpoint = drydock_svc_endpoint
        self.drydock_svc_type = drydock_svc_type
        self.drydock_task_id = drydock_task_id
        self.main_dag_name = main_dag_name
        self.node_filter = node_filter
        self.redeploy_server = redeploy_server
        self.shipyard_conf = shipyard_conf
        self.svc_token = svc_token
        self.sub_dag_name = sub_dag_name
        self.svc_session = svc_session
        self.svc_token = svc_token
        self.xcom_push_flag = xcom_push

    def execute(self, context):

        # Execute drydock base function
        self.drydock_base(context)

        # Exeute child function
        self.do_execute()

    def drydock_base(self, context):
        # Initialize Variables
        drydock_url = None
        dd_session = None

        # Define task_instance
        task_instance = context['task_instance']

        # Set up and retrieve values from xcom
        self.xcom_puller = XcomPuller(self.main_dag_name, task_instance)
        self.action_info = self.xcom_puller.get_action_info()
        self.dc = self.xcom_puller.get_deployment_configuration()

        # Logs uuid of action performed by the Operator
        logging.info("DryDock Operator for action %s", self.action_info['id'])

        # Retrieve information of the server that we want to redeploy if user
        # executes the 'redeploy_server' dag
        # Set node filter to be the server that we want to redeploy
        if self.action_info['dag_id'] == 'redeploy_server':
            self.redeploy_server = (
                self.action_info['parameters']['server-name'])

            if self.redeploy_server:
                logging.info("Server to be redeployed is %s",
                             self.redeploy_server)
                self.node_filter = self.redeploy_server
            else:
                raise AirflowException('Unable to retrieve information of '
                                       'node to be redeployed!')

        # Retrieve Endpoint Information
        self.drydock_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.drydock_svc_type)

        # Parse DryDock Service Endpoint
        drydock_url = urlparse(self.drydock_svc_endpoint)

        # Build a DrydockSession with credentials and target host
        # information.
        # The DrydockSession will care for TCP connection pooling
        # and header management
        logging.info("Build DryDock Session")
        dd_session = session.DrydockSession(drydock_url.hostname,
                                            port=drydock_url.port,
                                            auth_gen=self._auth_gen)

        # Raise Exception if we are not able to set up the session
        if dd_session:
            logging.info("Successfully Set Up DryDock Session")
        else:
            raise AirflowException("Failed to set up Drydock Session!")

        # Use the DrydockSession to build a DrydockClient that can
        # be used to make one or more API calls
        logging.info("Create DryDock Client")
        self.drydock_client = client.DrydockClient(dd_session)

        # Raise Exception if we are not able to build the client
        if self.drydock_client:
            logging.info("Successfully Set Up DryDock client")
        else:
            raise AirflowException("Failed to set up Drydock Client!")

        # Retrieve DeckHand Endpoint Information
        deckhand_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.deckhand_svc_type)

        logging.info("Deckhand endpoint is %s", deckhand_svc_endpoint)

        # Retrieve last committed revision id
        committed_revision_id = self.xcom_puller.get_design_version()

        # Form DeckHand Design Reference Path
        # This URL will be used to retrieve the Site Design YAMLs
        deckhand_path = "deckhand+" + deckhand_svc_endpoint
        self.deckhand_design_ref = os.path.join(deckhand_path,
                                                "revisions",
                                                str(committed_revision_id),
                                                "rendered-documents")
        if self.deckhand_design_ref:
            logging.info("Design YAMLs will be retrieved from %s",
                         self.deckhand_design_ref)
        else:
            raise AirflowException("Unable to Retrieve Design Reference!")

    @shipyard_service_token
    def _auth_gen(self):
        # Generator method for the Drydock Session to use to get the
        # auth headers necessary
        return [('X-Auth-Token', self.svc_token)]

    def create_task(self, task_action):

        # Initialize Variables
        create_task_response = {}

        # Node Filter
        logging.info("Nodes Filter List: %s", self.node_filter)

        try:
            # Create Task
            create_task_response = self.drydock_client.create_task(
                design_ref=self.deckhand_design_ref,
                task_action=task_action,
                node_filter=self.node_filter)

        except errors.ClientError as client_error:
            raise AirflowException(client_error)

        # Retrieve Task ID
        self.drydock_task_id = create_task_response['task_id']
        logging.info('Drydock %s task ID is %s',
                     task_action, self.drydock_task_id)

        # Raise Exception if we are not able to get the task_id from
        # Drydock
        if self.drydock_task_id:
            return self.drydock_task_id
        else:
            raise AirflowException("Unable to create task!")

    def query_task(self, interval, time_out):

        # Calculate number of times to execute the 'for' loop
        # Convert 'time_out' and 'interval' from string into integer
        # The result from the division will be a floating number which
        # We will round off to nearest whole number
        end_range = round(int(time_out) / int(interval))

        logging.info('Task ID is %s', self.drydock_task_id)

        # Query task status
        for i in range(0, end_range + 1):
            try:
                # Retrieve current task state
                task_state = self.drydock_client.get_task(
                    task_id=self.drydock_task_id)

                task_status = task_state['status']
                task_result = task_state['result']['status']

                logging.info("Current status of task id %s is %s",
                             self.drydock_task_id, task_status)

            except errors.ClientError as client_error:
                raise AirflowException(client_error)

            except:
                # There can be situations where there are intermittent network
                # issues that prevents us from retrieving the task state. We
                # will want to retry in such situations.
                logging.warning("Unable to retrieve task state. Retrying...")

            # Raise Time Out Exception
            if task_status == 'running' and i == end_range:
                raise AirflowException("Task Execution Timed Out!")

            # Exit 'for' loop if the task is in 'complete' or 'terminated'
            # state
            if task_status in ['complete', 'terminated']:
                logging.info('Task result is %s', task_result)
                break
            else:
                time.sleep(int(interval))

        # Get final task result
        if task_result == 'success':
            logging.info('Task id %s has been successfully completed',
                         self.drydock_task_id)
        else:
            raise AirflowException("Failed to execute/complete task!")


class DrydockBaseOperatorPlugin(AirflowPlugin):

    """Creates DrydockBaseOperator in Airflow."""

    name = 'drydock_base_operator_plugin'
    operators = [DrydockBaseOperator]
