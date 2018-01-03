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

import configparser
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
from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token


class DryDockOperator(BaseOperator):
    """
    DryDock Client
    :param action: Task to perform
    :param design_ref: A URI reference to the design documents
    :param main_dag_name: Parent Dag
    :param node_filter: A filter for narrowing the scope of the task. Valid
                        fields are 'node_names', 'rack_names', 'node_tags'
    :param shipyard_conf: Location of shipyard.conf
    :param sub_dag_name: Child Dag
    :param workflow_info: Information related to the workflow
    """
    @apply_defaults
    def __init__(self,
                 action=None,
                 design_ref=None,
                 main_dag_name=None,
                 node_filter=None,
                 shipyard_conf=None,
                 sub_dag_name=None,
                 workflow_info={},
                 xcom_push=True,
                 *args, **kwargs):

        super(DryDockOperator, self).__init__(*args, **kwargs)
        self.action = action
        self.design_ref = design_ref
        self.main_dag_name = main_dag_name
        self.node_filter = node_filter
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.workflow_info = workflow_info
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        # Initialize Variables
        context['svc_type'] = 'physicalprovisioner'
        genesis_node_ip = None

        # Placeholder definition
        # TODO: Need to decide how to pass the required value from Shipyard to
        # the 'node_filter' variable. No filter will be used for now.
        self.node_filter = None

        # Define task_instance
        task_instance = context['task_instance']

        # Extract information related to current workflow
        # The workflow_info variable will be a dictionary
        # that contains information about the workflow such
        # as action_id, name and other related parameters
        workflow_info = task_instance.xcom_pull(
            task_ids='action_xcom', key='action',
            dag_id=self.main_dag_name)

        # Logs uuid of action performed by the Operator
        logging.info("DryDock Operator for action %s", workflow_info['id'])

        # DrydockClient
        if self.action == 'create_drydock_client':
            # Retrieve Endpoint Information
            context['svc_endpoint'] = ucp_service_endpoint(self, context)
            logging.info("DryDock endpoint is %s", context['svc_endpoint'])

            # Set up DryDock Client
            drydock_client = self.drydock_session_client(context)

            return drydock_client

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

            # Reset 'svc_type' to DryDock instead of DeckHand
            context['svc_type'] = 'physicalprovisioner'

            # Retrieve Endpoint Information
            context['svc_endpoint'] = ucp_service_endpoint(self, context)

            site_design_validity = self.drydock_validate_design(context)

            return site_design_validity

        # Retrieve drydock_client via XCOM so as to perform other tasks
        drydock_client = task_instance.xcom_pull(
            task_ids='create_drydock_client',
            dag_id=self.main_dag_name + '.' + self.sub_dag_name)

        # Read shipyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        if not config.read(self.shipyard_conf):
            raise AirflowException("Unable to read content of shipyard.conf")

        # Create Task for verify_site
        if self.action == 'verify_site':

            # Default settings for 'verify_site' execution is to query
            # the task every 10 seconds and to time out after 60 seconds
            query_interval = config.get('drydock',
                                        'verify_site_query_interval')
            task_timeout = config.get('drydock', 'verify_site_task_timeout')

            self.drydock_action(drydock_client, context, self.action,
                                query_interval, task_timeout)

        # Create Task for prepare_site
        elif self.action == 'prepare_site':
            # Default settings for 'prepare_site' execution is to query
            # the task every 10 seconds and to time out after 120 seconds
            query_interval = config.get('drydock',
                                        'prepare_site_query_interval')
            task_timeout = config.get('drydock', 'prepare_site_task_timeout')

            self.drydock_action(drydock_client, context, self.action,
                                query_interval, task_timeout)

        # Create Task for prepare_node
        elif self.action == 'prepare_nodes':
            # Default settings for 'prepare_node' execution is to query
            # the task every 30 seconds and to time out after 1800 seconds
            query_interval = config.get('drydock',
                                        'prepare_node_query_interval')
            task_timeout = config.get('drydock', 'prepare_node_task_timeout')

            self.drydock_action(drydock_client, context, self.action,
                                query_interval, task_timeout)

        # Create Task for deploy_node
        elif self.action == 'deploy_nodes':
            # Default settings for 'deploy_node' execution is to query
            # the task every 30 seconds and to time out after 3600 seconds
            query_interval = config.get('drydock',
                                        'deploy_node_query_interval')
            task_timeout = config.get('drydock', 'deploy_node_task_timeout')

            self.drydock_action(drydock_client, context, self.action,
                                query_interval, task_timeout)

            # Wait for 120 seconds (default value) before checking the cluster
            # join process as it takes time for process to be triggered across
            # all nodes
            cluster_join_check_backoff_time = config.get(
                'drydock', 'cluster_join_check_backoff_time')
            logging.info("All nodes deployed in MAAS")
            logging.info("Wait for %d seconds before checking node state...",
                         int(cluster_join_check_backoff_time))
            time.sleep(int(cluster_join_check_backoff_time))

            # Check that cluster join process is completed before declaring
            # deploy_node as 'completed'. Set time out to 30 minutes and set
            # polling interval to 30 seconds.
            check_node_status(1800, 30)

        # Do not perform any action
        else:
            logging.info('No Action to Perform')

    @shipyard_service_token
    def drydock_session_client(self, context):
        # Initialize Variables
        drydock_url = None
        dd_session = None
        dd_client = None

        # Parse DryDock Service Endpoint
        drydock_url = urlparse(context['svc_endpoint'])

        # Build a DrydockSession with credentials and target host
        # information.
        logging.info("Build DryDock Session")
        dd_session = session.DrydockSession(drydock_url.hostname,
                                            port=drydock_url.port,
                                            token=context['svc_token'])

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
                                            action, None)

        logging.info('Task ID is %s', task_id)

        # Query Task
        self.drydock_query_task(drydock_client, interval, time_out,
                                task_id)

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

    def drydock_query_task(self, drydock_client, interval, time_out, task_id):

        # Calculate number of times to execute the 'for' loop
        # Convert 'time_out' and 'interval' from string into integer
        # The result from the division will be a floating number which
        # We will round off to nearest whole number
        end_range = round(int(time_out) / int(interval))

        # Query task status
        for i in range(0, end_range + 1):

            try:
                # Retrieve current task state
                task_state = drydock_client.get_task(task_id=task_id)
                task_status = task_state.get('status')
                task_result = task_state.get('result')['status']

                logging.info("Current status of task id %s is %s",
                             task_id, task_status)
            except:
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
        # NOTE: The promenade join script does not have a call-back step
        # to indicate that the process is completed at the moment. This
        # will lead to Drydock returning 'partial success' at the end of
        # the 'deploy_nodes' task as it times out while waiting for the
        # response from promenade (bootactions will fail as a result). As
        # such, we are keeping 'partial_success' as a valid task result
        # for now and will update the Drydock Operator once the promenade
        # feature is ready for consumption.
        if task_result in ['success', 'partial_success']:
            logging.info('Task id %s has been successfully completed',
                         self.task_id)
        else:
            raise AirflowException("Failed to execute/complete task!")

    def get_deckhand_design_ref(self, context):

        # Retrieve DeckHand Endpoint Information
        context['svc_type'] = 'deckhand'
        context['svc_endpoint'] = ucp_service_endpoint(self, context)
        logging.info("Deckhand endpoint is %s", context['svc_endpoint'])

        # Retrieve revision_id from xcom
        # Note that in the case of 'deploy_site', the dag_id will
        # be 'deploy_site.deckhand_get_design_version' for the
        # 'deckhand_get_design_version' task. We need to extract
        # the xcom value from it in order to get the value of the
        # last committed revision ID
        committed_revision_id = context['task_instance'].xcom_pull(
            task_ids='deckhand_get_design_version',
            dag_id=self.main_dag_name + '.deckhand_get_design_version')

        # Form DeckHand Design Reference Path that we will use to retrieve
        # the DryDock YAMLs
        deckhand_path = "deckhand+" + context['svc_endpoint']
        deckhand_design_ref = os.path.join(deckhand_path,
                                           "revisions",
                                           str(committed_revision_id),
                                           "rendered-documents")

        return deckhand_design_ref

    @shipyard_service_token
    def drydock_validate_design(self, context):

        # Form Validation Endpoint
        validation_endpoint = os.path.join(context['svc_endpoint'],
                                           'validatedesign')

        logging.info("Validation Endpoint is %s", validation_endpoint)

        # Define Headers and Payload
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': context['svc_token']
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
