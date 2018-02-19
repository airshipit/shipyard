# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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

import json
import logging
import os
import requests
import time
from urllib.parse import urlparse

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

import drydock_provisioner.drydock_client.client as client
import drydock_provisioner.drydock_client.session as session
from check_k8s_node_status import check_node_status
from drydock_provisioner import error as errors
from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token
from xcom_puller import XcomPuller


class DryDockOperator(BaseOperator):
    """DryDock Client"""
    @apply_defaults
    def __init__(self,
                 action=None,
                 design_ref=None,
                 main_dag_name=None,
                 node_filter=None,
                 shipyard_conf=None,
                 svc_token=None,
                 sub_dag_name=None,
                 xcom_push=True,
                 *args, **kwargs):
        """
        :param action: Task to perform
        :param design_ref: A URI reference to the design documents
        :param main_dag_name: Parent Dag
        :param node_filter: A filter for narrowing the scope of the task. Valid
                            fields are 'node_names', 'rack_names', 'node_tags'
        :param shipyard_conf: Location of shipyard.conf
        :param sub_dag_name: Child Dag

        The Drydock operator assumes that prior steps have set xcoms for
        the action and the deployment configuration
        """

        super(DryDockOperator, self).__init__(*args, **kwargs)
        self.action = action
        self.design_ref = design_ref
        self.main_dag_name = main_dag_name
        self.node_filter = node_filter
        self.shipyard_conf = shipyard_conf
        self.svc_token = svc_token
        self.sub_dag_name = sub_dag_name
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        # Initialize Variable
        redeploy_server = None

        # Placeholder definition
        # TODO: Need to decide how to pass the required value from Shipyard to
        # the 'node_filter' variable. No filter will be used for now.
        self.node_filter = None

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
            redeploy_server = self.action_info['parameters'].get('server-name')

            if redeploy_server:
                logging.info("Server to be redeployed is %s", redeploy_server)
                self.node_filter = redeploy_server
            else:
                raise AirflowException('Unable to retrieve information of '
                                       'node to be redeployed!')

        # Retrieve Deckhand Design Reference
        self.design_ref = self.get_deckhand_design_ref(context)

        if self.design_ref:
            logging.info("Drydock YAMLs will be retrieved from %s",
                         self.design_ref)
        else:
            raise AirflowException("Unable to Retrieve Design Reference!")

        # Drydock Validate Site Design
        if self.action == 'validate_site_design':
            # Initialize variable
            site_design_validity = 'invalid'

            # Retrieve Endpoint Information
            svc_type = 'physicalprovisioner'
            drydock_svc_endpoint = ucp_service_endpoint(self,
                                                        svc_type=svc_type)

            site_design_validity = self.drydock_validate_design(
                drydock_svc_endpoint)

            return site_design_validity

        # DrydockClient
        # Retrieve Endpoint Information
        svc_type = 'physicalprovisioner'
        drydock_svc_endpoint = ucp_service_endpoint(self,
                                                    svc_type=svc_type)
        logging.info("DryDock endpoint is %s", drydock_svc_endpoint)

        # Set up DryDock Client
        drydock_client = self.drydock_session_client(drydock_svc_endpoint)

        # Create Task for verify_site
        if self.action == 'verify_site':
            q_interval = self.dc['physical_provisioner.verify_interval']
            task_timeout = self.dc['physical_provisioner.verify_timeout']
            self.drydock_action(drydock_client, context, self.action,
                                q_interval, task_timeout)

        # Create Task for prepare_site
        elif self.action == 'prepare_site':
            q_interval = self.dc['physical_provisioner.prepare_site_interval']
            task_timeout = self.dc['physical_provisioner.prepare_site_timeout']
            self.drydock_action(drydock_client, context, self.action,
                                q_interval, task_timeout)

        # Create Task for prepare_node
        elif self.action == 'prepare_nodes':
            q_interval = self.dc['physical_provisioner.prepare_node_interval']
            task_timeout = self.dc['physical_provisioner.prepare_node_timeout']
            self.drydock_action(drydock_client, context, self.action,
                                q_interval, task_timeout)

        # Create Task for deploy_node
        elif self.action == 'deploy_nodes':
            q_interval = self.dc['physical_provisioner.deploy_interval']
            task_timeout = self.dc['physical_provisioner.deploy_timeout']
            self.drydock_action(drydock_client, context, self.action,
                                q_interval, task_timeout)

            # Wait for 120 seconds (default value) before checking the cluster
            # join process as it takes time for process to be triggered across
            # all nodes
            join_wait = self.dc['physical_provisioner.join_wait']
            logging.info("All nodes deployed in MAAS")
            logging.info("Wait for %d seconds before checking node state...",
                         join_wait)
            time.sleep(join_wait)
            # Check that cluster join process is completed before declaring
            # deploy_node as 'completed'.
            node_st_timeout = self.dc['kubernetes.node_status_timeout']
            node_st_interval = self.dc['kubernetes.node_status_interval']
            check_node_status(node_st_timeout, node_st_interval)

        # Create Task for destroy_node
        # NOTE: This is a PlaceHolder function. The 'destroy_node'
        # functionalities in DryDock is being worked on and is not
        # ready at the moment.
        elif self.action == 'destroy_node':
            # see deployment_configuration_operator.py for defaults
            q_interval = self.dc['physical_provisioner.destroy_interval']
            task_timeout = self.dc['physical_provisioner.destroy_timeout']

            logging.info("Destroying node %s from cluster...", redeploy_server)
            time.sleep(15)
            logging.info("Successfully deleted node %s", redeploy_server)

            # TODO: Uncomment when the function to destroy/delete node is
            # ready for consumption in Drydock
            # self.drydock_action(drydock_client, context, self.action,
            #                    q_interval, task_timeout)

        # Do not perform any action
        else:
            logging.info('No Action to Perform')

    @shipyard_service_token
    def _auth_gen(self):
        # Generator method for the Drydock Session to use to get the
        # auth headers necessary
        return [('X-Auth-Token', self.svc_token)]

    def drydock_session_client(self, drydock_svc_endpoint):
        # Initialize Variables
        drydock_url = None
        dd_session = None
        dd_client = None

        # Parse DryDock Service Endpoint
        drydock_url = urlparse(drydock_svc_endpoint)

        # Build a DrydockSession with credentials and target host
        # information.
        logging.info("Build DryDock Session")
        dd_session = session.DrydockSession(drydock_url.hostname,
                                            port=drydock_url.port,
                                            auth_gen=self._auth_gen)

        # Raise Exception if we are not able to get a drydock session
        if dd_session:
            logging.info("Successfully Set Up DryDock Session")
        else:
            raise AirflowException("Failed to set up Drydock Session!")

        # Use session to build a DrydockClient to make one or more API calls
        # The DrydockSession will care for TCP connection pooling
        # and header management
        logging.info("Create DryDock Client")
        dd_client = client.DrydockClient(dd_session)

        # Raise Exception if we are not able to build drydock client
        if dd_client:
            logging.info("Successfully Set Up DryDock client")
        else:
            raise AirflowException("Unable to set up Drydock Client!")

        # Drydock client for XCOM Usage
        return dd_client

    def drydock_action(self, drydock_client, context, action, interval,
                       time_out):

        # Trigger DryDock to execute task and retrieve task ID
        task_id = self.drydock_perform_task(drydock_client, context,
                                            action, self.node_filter)

        logging.info('Task ID is %s', task_id)

        # Query Task
        self.drydock_query_task(drydock_client, context, interval,
                                time_out, task_id)

    def drydock_perform_task(self, drydock_client, context,
                             perform_task, nodes_filter):

        # Initialize Variables
        create_task_response = {}
        task_id = None

        # Node Filter
        logging.info("Nodes Filter List: %s", nodes_filter)

        # Create Task
        create_task_response = drydock_client.create_task(
            design_ref=self.design_ref,
            task_action=perform_task,
            node_filter=nodes_filter)

        # Retrieve Task ID
        task_id = create_task_response.get('task_id')
        logging.info('Drydock %s task ID is %s', perform_task, task_id)

        # Raise Exception if we are not able to get the task_id from
        # drydock
        if task_id:
            return task_id
        else:
            raise AirflowException("Unable to create task!")

    def drydock_query_task(self, drydock_client, context, interval,
                           time_out, task_id):

        # Initialize Variables
        keystone_token_expired = False
        new_dd_client = None
        dd_client = drydock_client

        # Calculate number of times to execute the 'for' loop
        # Convert 'time_out' and 'interval' from string into integer
        # The result from the division will be a floating number which
        # We will round off to nearest whole number
        end_range = round(int(time_out) / int(interval))

        # Query task status
        for i in range(0, end_range + 1):

            if keystone_token_expired:
                logging.info("Established new drydock session")
                dd_client = new_dd_client

            try:
                # Retrieve current task state
                task_state = dd_client.get_task(task_id=task_id)
                task_status = task_state.get('status')
                task_result = task_state.get('result')['status']

                logging.info("Current status of task id %s is %s",
                             task_id, task_status)

                keystone_token_expired = False

            except errors.ClientUnauthorizedError as unauthorized_error:

                # TODO: This is a temporary workaround. Drydock will be
                # updated with the appropriate fix in the drydock api
                # client by having the session detect a 401/403 response
                # and refresh the token appropriately.
                # Logs drydock client unauthorized error
                keystone_token_expired = True
                logging.error(unauthorized_error)

                # Set up new drydock client with new keystone token
                logging.info("Setting up new drydock session...")

                drydock_svc_endpoint = ucp_service_endpoint(
                    self, svc_type='physicalprovisioner')

                new_dd_client = self.drydock_session_client(
                    drydock_svc_endpoint)

            except errors.ClientForbiddenError as forbidden_error:
                raise AirflowException(forbidden_error)

            except errors.ClientError as client_error:
                raise AirflowException(client_error)

            except:
                # There can be instances where there are intermittent network
                # issues that prevents us from retrieving the task state. We
                # will want to retry in such situations.
                logging.info("Unable to retrieve task state. Retrying...")

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
                         self.task_id)
        else:
            raise AirflowException("Failed to execute/complete task!")

    def get_deckhand_design_ref(self, context):

        # Retrieve DeckHand Endpoint Information
        svc_type = 'deckhand'
        deckhand_svc_endpoint = ucp_service_endpoint(self,
                                                     svc_type=svc_type)
        logging.info("Deckhand endpoint is %s", deckhand_svc_endpoint)

        committed_revision_id = self.xcom_puller.get_design_version()

        # Form DeckHand Design Reference Path that we will use to retrieve
        # the DryDock YAMLs
        deckhand_path = "deckhand+" + deckhand_svc_endpoint
        deckhand_design_ref = os.path.join(deckhand_path,
                                           "revisions",
                                           str(committed_revision_id),
                                           "rendered-documents")

        return deckhand_design_ref

    @shipyard_service_token
    def drydock_validate_design(self, drydock_svc_endpoint):

        # Form Validation Endpoint
        validation_endpoint = os.path.join(drydock_svc_endpoint,
                                           'validatedesign')

        logging.info("Validation Endpoint is %s", validation_endpoint)

        # Define Headers and Payload
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.svc_token
        }

        payload = {
            'rel': "design",
            'href': self.design_ref,
            'type': "application/x-yaml"
        }

        # Requests DryDock to validate site design
        logging.info("Waiting for DryDock to validate site design...")

        try:
            design_validate_response = requests.post(validation_endpoint,
                                                     headers=headers,
                                                     data=json.dumps(payload))
        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        # Convert response to string
        validate_site_design = design_validate_response.text

        # Print response
        logging.info("Retrieving DryDock validate site design response...")
        logging.info(json.loads(validate_site_design))

        # Check if site design is valid
        if json.loads(validate_site_design).get('status') == 'Success':
            logging.info("DryDock Site Design has been successfully validated")
            return 'valid'
        else:
            raise AirflowException("DryDock Site Design Validation Failed!")


class DryDockClientPlugin(AirflowPlugin):
    name = "drydock_client_plugin"
    operators = [DryDockOperator]
