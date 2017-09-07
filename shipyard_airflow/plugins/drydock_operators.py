# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import subprocess
import os
import time
import re
import configparser

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

import drydock_provisioner.drydock_client.client as client
import drydock_provisioner.drydock_client.session as session


class DryDockOperator(BaseOperator):
    """
    DryDock Client
    :host: Target Host
    :port: DryDock Port
    :token: DryDock Token
    :shipyard_conf: Location of shipyard.conf
    :drydock_conf: Location of drydock YAML
    :promenade_conf: Location of promenade YAML
    :action: Task to perform
    :design_id: DryDock Design ID
    :workflow_info: Information related to the workflow
    :main_dag_name: Parent Dag
    :sub_dag_name: Child Dag
    """
    @apply_defaults
    def __init__(self,
                 host=None,
                 port=None,
                 token=None,
                 action=None,
                 design_id=None,
                 shipyard_conf=None,
                 drydock_conf=None,
                 promenade_conf=None,
                 workflow_info={},
                 main_dag_name=None,
                 sub_dag_name=None,
                 xcom_push=True,
                 *args, **kwargs):

        super(DryDockOperator, self).__init__(*args, **kwargs)
        self.host = host
        self.port = port
        self.token = token
        self.shipyard_conf = shipyard_conf
        self.drydock_conf = drydock_conf
        self.promenade_conf = promenade_conf
        self.action = action
        self.design_id = design_id
        self.workflow_info = workflow_info
        self.main_dag_name = main_dag_name
        self.sub_dag_name = sub_dag_name
        self.xcom_push_flag = xcom_push

    def execute(self, context):
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
            drydock_client = self.drydock_session_client(context)

            return drydock_client

        # Retrieve drydock_client via XCOM so as to perform other tasks
        drydock_client = task_instance.xcom_pull(
            task_ids='create_drydock_client',
            dag_id=self.sub_dag_name + '.create_drydock_client')

        # Get Design ID
        if self.action == 'get_design_id':
            design_id = self.drydock_create_design(drydock_client)

            return design_id

        # DryDock Load Parts
        elif self.action == 'drydock_load_parts':
            self.parts_type = 'drydock'
            self.load_parts(drydock_client, context, self.parts_type)

        # Promenade Load Parts
        elif self.action == 'promenade_load_parts':
            self.parts_type = 'promenade'
            self.load_parts(drydock_client, context, self.parts_type)

        # Create Task for verify_site
        elif self.action == 'verify_site':
            self.perform_task = 'verify_site'
            verify_site = self.drydock_perform_task(drydock_client, context,
                                                    self.perform_task, None)

            # Define variables
            # Query every 10 seconds for 1 minute
            interval = 10
            time_out = 60
            desired_state = 'success'

            # Query verify_site Task
            task_id = verify_site['task_id']
            logging.info(task_id)
            verify_site_status = self.drydock_query_task(drydock_client,
                                                         interval,
                                                         time_out,
                                                         task_id,
                                                         desired_state)

            if verify_site_status == 'timed_out':
                raise AirflowException('Verify_Site Task Timed Out!')
            elif verify_site_status == 'task_failed':
                raise AirflowException('Verify_Site Task Failed!')
            else:
                logging.info('Verify Site Task:')
                logging.info(verify_site_status)

        # Create Task for prepare_site
        elif self.action == 'prepare_site':
            self.perform_task = 'prepare_site'
            prepare_site = self.drydock_perform_task(drydock_client, context,
                                                     self.perform_task, None)

            # Define variables
            # Query every 10 seconds for 2 minutes
            interval = 10
            time_out = 120
            desired_state = 'partial_success'

            # Query prepare_site Task
            task_id = prepare_site['task_id']
            logging.info(task_id)
            prepare_site_status = self.drydock_query_task(drydock_client,
                                                          interval,
                                                          time_out,
                                                          task_id,
                                                          desired_state)

            if prepare_site_status == 'timed_out':
                raise AirflowException('Prepare_Site Task Timed Out!')
            elif prepare_site_status == 'task_failed':
                raise AirflowException('Prepare_Site Task Failed!')
            else:
                logging.info('Prepare Site Task:')
                logging.info(prepare_site_status)

        # Create Task for prepare_node
        elif self.action == 'prepare_node':
            self.perform_task = 'prepare_node'
            prepare_node = self.drydock_perform_task(
                drydock_client, context,
                self.perform_task, workflow_info)

            # Define variables
            # Query every 30 seconds for 30 minutes
            interval = 30
            time_out = 1800
            desired_state = 'success'

            # Query prepare_node Task
            task_id = prepare_node['task_id']
            logging.info(task_id)
            prepare_node_status = self.drydock_query_task(drydock_client,
                                                          interval,
                                                          time_out,
                                                          task_id,
                                                          desired_state)

            if prepare_node_status == 'timed_out':
                raise AirflowException('Prepare_Node Task Timed Out!')
            elif prepare_node_status == 'task_failed':
                raise AirflowException('Prepare_Node Task Failed!')
            else:
                logging.info('Prepare Node Task:')
                logging.info(prepare_node_status)

        # Create Task for deploy_node
        elif self.action == 'deploy_node':
            self.perform_task = 'deploy_node'
            deploy_node = self.drydock_perform_task(drydock_client,
                                                    context,
                                                    self.perform_task,
                                                    workflow_info)

            # Define variables
            # Query every 30 seconds for 60 minutes
            interval = 30
            time_out = 3600
            desired_state = 'success'

            # Query deploy_node Task
            task_id = deploy_node['task_id']
            logging.info(task_id)
            deploy_node_status = self.drydock_query_task(drydock_client,
                                                         interval,
                                                         time_out,
                                                         task_id,
                                                         desired_state)

            if deploy_node_status == 'timed_out':
                raise AirflowException('Deploy_Node Task Timed Out!')
            elif deploy_node_status == 'task_failed':
                raise AirflowException('Deploy_Node Task Failed!')
            else:
                logging.info('Deploy Node Task:')
                logging.info(deploy_node_status)
        else:
            logging.info('No Action to Perform')

    def keystone_token_get(self, conf_path):

        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(conf_path)

        # Construct Envrionment variables
        for attr in ('OS_AUTH_URL', 'OS_PROJECT_NAME', 'OS_USER_DOMAIN_NAME',
                     'OS_USERNAME', 'OS_PASSWORD', 'OS_REGION_NAME',
                     'OS_IDENTITY_API_VERSION'):
            os.environ[attr] = config.get('keystone', attr)

        # Execute 'openstack token issue' command
        logging.info("Get Keystone Token")
        keystone_output = subprocess.Popen(["openstack", "token", "issue"],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)

        # Get Keystone Token from output
        line = ''
        for line in iter(keystone_output.stdout.readline, b''):
            line = line.strip()
            if re.search(r'\bid\b', str(line, 'utf-8')):
                token = str(line, 'utf-8').split(' |')[1].split(' ')[1]

        # Wait for child process to terminate
        # Set and return returncode attribute.
        keystone_output.wait()
        logging.info(
            "Command exited with "
            "return code {0}".format(keystone_output.returncode))

        # Raise Execptions if 'openstack token issue' fails to execute
        if keystone_output.returncode:
            raise AirflowException("Unable to get Keystone Token!")
            return 'keystone_token_error'
        else:
            logging.info(token)
            return token

    def drydock_session_client(self, context):

        # Retrieve Keystone Token
        keystone_token = self.keystone_token_get(self.shipyard_conf)

        # Raise Exception and Exit if we are not able to get Keystone
        # Token, else continue
        if keystone_token == 'keystone_token_error':
            raise AirflowException("Unable to get Keystone Token!")
        else:
            pass

        # Build a DrydockSession with credentials and target host
        # information.  Note that hard-coded token will be replaced
        # by keystone_token in near future
        logging.info("Build DryDock Session")
        dd_session = session.DrydockSession(self.host, port=self.port,
                                            token=self.token)

        # Raise Exception if we are not able to get a drydock session
        if dd_session:
            pass
        else:
            raise AirflowException("Unable to get a drydock session")

        # Use session to build a DrydockClient to make one or more API calls
        # The DrydockSession will care for TCP connection pooling
        # and header management
        logging.info("Create DryDock Client")
        dd_client = client.DrydockClient(dd_session)

        # Raise Exception if we are not able to build drydock client
        if dd_client:
            pass
        else:
            raise AirflowException("Unable to build drydock client")

        # Drydock client for XCOM Usage
        return dd_client

    def drydock_create_design(self, drydock_client):

        # Create Design
        logging.info('Create Design ID')
        drydock_design_id = drydock_client.create_design()

        # Raise Exception if we are not able to get a value
        # from drydock create_design API call
        if drydock_design_id:
            return drydock_design_id
        else:
            raise AirflowException("Unable to create Design ID")

    def get_design_id(self, context):

        # Get Design ID from XCOM
        task_instance = context['task_instance']
        design_id = task_instance.xcom_pull(
            task_ids='drydock_get_design_id',
            dag_id=self.sub_dag_name + '.drydock_get_design_id')

        return design_id

    def load_parts(self, drydock_client, context, parts_type):

        # Load new design parts into a design context via YAML conforming
        # to the Drydock design YAML schema

        # Open drydock.yaml/promenade.yaml as string so that it can be
        # ingested.  This step will change in future when DeckHand is
        # integrated with the system
        if self.parts_type == 'drydock':
            with open(self.drydock_conf, "r") as drydock_yaml:
                yaml_string = drydock_yaml.read()
        else:
            with open(self.promenade_conf, "r") as promenade_yaml:
                yaml_string = promenade_yaml.read()

        # Get Design ID and pass it to DryDock
        self.design_id = self.get_design_id(context)

        # Load Design
        # Return Exception if list is empty
        logging.info("Load %s Configuration Yaml", self.parts_type)
        load_design = drydock_client.load_parts(self.design_id,
                                                yaml_string=yaml_string)

        if len(load_design) == 0:
            raise AirflowException("Empty Design.  Please check input Yaml.")
        else:
            logging.info(load_design)

    def drydock_perform_task(self, drydock_client, context,
                             perform_task, workflow_info):

        # Get Design ID and pass it to DryDock
        self.design_id = self.get_design_id(context)

        # Task to do
        task_to_perform = self.perform_task

        # Node Filter
        if workflow_info:
            nodes_filter = workflow_info['parameters']['servername']
        else:
            nodes_filter = None

        logging.info("Nodes Filter List: %s", nodes_filter)

        # Get uuid of the create_task's id
        self.task_id = drydock_client.create_task(self.design_id,
                                                  task_to_perform,
                                                  nodes_filter)

        # Get current state/response of the drydock task
        task_status = drydock_client.get_task(self.task_id)

        # task_status should contain information and be of length > 0
        # Raise Exception if that is not the case
        if len(task_status) == 0:
            raise AirflowException("Unable to get task state")
        else:
            return task_status

    def drydock_query_task(self, drydock_client, interval, time_out,
                           task_id, desired_state):

            # Calculate number of times to execute the 'for' loop
            end_range = int(time_out / interval)

            # Query task state
            for i in range(0, end_range + 1):

                # Retrieve current task state
                task_state = drydock_client.get_task(self.task_id)
                logging.info(task_state)

                # Return Time Out Exception
                if task_state['status'] == 'running' and i == end_range:
                    logging.info('Timed Out!')
                    return 'timed_out'

                # Exit 'for' loop if task is in 'complete' state
                if task_state['status'] == 'complete':
                    break
                else:
                    time.sleep(interval)

            # Get final task state
            if task_state['result'] == desired_state:
                return drydock_client.get_task(self.task_id)
            else:
                return 'task_failed'

class DryDockClientPlugin(AirflowPlugin):
    name = "drydock_client_plugin"
    operators = [DryDockOperator]
