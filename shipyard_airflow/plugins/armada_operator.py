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

import logging
import os
import requests
from urllib.parse import urlparse

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

import armada.common.client as client
import armada.common.session as session
from get_k8s_pod_port_ip import get_pod_port_ip
from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token


class ArmadaOperator(BaseOperator):
    """
    Supports interaction with Armada
    :param action: Task to perform
    :param main_dag_name: Parent Dag
    :param shipyard_conf: Location of shipyard.conf
    :param sub_dag_name: Child Dag
    """

    @apply_defaults
    def __init__(self,
                 action=None,
                 main_dag_name=None,
                 shipyard_conf=None,
                 sub_dag_name=None,
                 workflow_info={},
                 xcom_push=True,
                 *args, **kwargs):

        super(ArmadaOperator, self).__init__(*args, **kwargs)
        self.action = action
        self.main_dag_name = main_dag_name
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.workflow_info = workflow_info
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        # Initialize Variables
        context['svc_type'] = 'armada'
        armada_client = None

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
        logging.info("Armada Operator for action %s", workflow_info['id'])

        # Create Armada Client
        if self.action == 'create_armada_client':
            # Retrieve Endpoint Information
            context['svc_endpoint'] = ucp_service_endpoint(self, context)
            logging.info("Armada endpoint is %s", context['svc_endpoint'])

            # Set up Armada Client
            session_client = self.armada_session_client(context)

            return session_client

        # Retrieve armada_client via XCOM so as to perform other tasks
        armada_client = task_instance.xcom_pull(
            task_ids='create_armada_client',
            dag_id=self.sub_dag_name + '.create_armada_client')

        # Retrieve Tiller Information and assign to context 'query'
        context['query'] = self.get_tiller_info(context)

        # Retrieve Genesis Node IP and assign it to context 'genesis_ip'
        context['genesis_ip'] = self.get_genesis_node_info(context)

        # Armada API Call
        # Armada Status
        if self.action == 'armada_status':
            self.get_armada_status(context, armada_client)

        # Armada Validate
        elif self.action == 'armada_validate':
            self.armada_validate(context, armada_client)

        # Armada Apply
        elif self.action == 'armada_apply':
            self.armada_apply(context, armada_client)

        # Armada Get Releases
        elif self.action == 'armada_get_releases':
            self.armada_get_releases(context, armada_client)

        else:
            logging.info('No Action to Perform')

    @shipyard_service_token
    def armada_session_client(self, context):
        # Initialize Variables
        armada_url = None
        a_session = None
        a_client = None

        # Parse Armada Service Endpoint
        armada_url = urlparse(context['svc_endpoint'])

        # Build a ArmadaSession with credentials and target host
        # information.
        logging.info("Build Armada Session")
        a_session = session.ArmadaSession(armada_url.hostname,
                                          port=armada_url.port,
                                          token=context['svc_token'])

        # Raise Exception if we are not able to get armada session
        if a_session:
            logging.info("Successfully Set Up Armada Session")
        else:
            raise AirflowException("Failed to set up Armada Session!")

        # Use session to build a ArmadaClient to make one or more
        # API calls.  The ArmadaSession will care for TCP connection
        # pooling and header management
        logging.info("Create Armada Client")
        a_client = client.ArmadaClient(a_session)

        # Raise Exception if we are not able to build armada client
        if a_client:
            logging.info("Successfully Set Up Armada client")
        else:
            raise AirflowException("Failed to set up Armada client!")

        # Return Armada client for XCOM Usage
        return a_client

    @get_pod_port_ip('tiller')
    def get_tiller_info(self, context, *args):
        # Initialize Variable
        query = {}

        # Get IP and port information of Pods from context
        k8s_pods_ip_port = context['pods_ip_port']

        # Assign value to the 'query' dictionary so that we can pass
        # it via the Armada Client
        query['tiller_host'] = k8s_pods_ip_port['tiller'].get('ip')
        query['tiller_port'] = k8s_pods_ip_port['tiller'].get('port')

        return query

    def get_armada_status(self, context, armada_client):
        # Check State of Tiller
        armada_status = armada_client.get_status(context['query'])

        # Tiller State will return boolean value, i.e. True/False
        # Raise Exception if Tiller is in a bad state
        if armada_status['tiller']['state']:
            logging.info("Tiller is in running state")
            logging.info("Tiller version is %s",
                         armada_status['tiller']['version'])
        else:
            raise AirflowException("Please check Tiller!")

    def armada_validate(self, context, armada_client):
        # Initialize Variables
        armada_manifest = None
        valid_armada_yaml = {}

        # Retrieve Armada Manifest
        armada_manifest = self.get_armada_yaml(context)

        # Validate armada yaml file
        logging.info("Armada Validate")
        valid_armada_yaml = armada_client.post_validate(armada_manifest)

        # The response will be a dictionary indicating whether the yaml
        # file is valid or invalid.  We will check the Boolean value in
        # this case.
        if valid_armada_yaml['valid']:
            logging.info("Armada Yaml File is Valid")
        else:
            raise AirflowException("Invalid Armada Yaml File!")

    def armada_apply(self, context, armada_client):
        # Initialize Variables
        armada_manifest = None
        armada_post_apply = {}
        override_values = []
        chart_set = []

        # Retrieve Armada Manifest
        armada_manifest = self.get_armada_yaml(context)

        # Execute Armada Apply to install the helm charts in sequence
        logging.info("Armada Apply")
        armada_post_apply = armada_client.post_apply(armada_manifest,
                                                     override_values,
                                                     chart_set,
                                                     context['query'])

        # We will expect Armada to return the releases that it is
        # deploying. An empty value for 'install' means that armada
        # delploy has failed. Note that if we try and deploy the
        # same release twice, we will end up with empty response on
        # our second attempt and that will be treated as a failure
        # scenario.
        if armada_post_apply['message']['install']:
            logging.info("Armada Apply Successfully Executed")
            logging.info(armada_post_apply)
        else:
            logging.info(armada_post_apply)
            raise AirflowException("Armada Apply Failed!")

    def armada_get_releases(self, context, armada_client):
        # Initialize Variables
        armada_releases = {}

        # Retrieve Armada Releases after deployment
        logging.info("Retrieving Armada Releases after deployment..")
        armada_releases = armada_client.get_releases(context['query'])

        if armada_releases:
            logging.info("Retrieved current Armada Releases")
            logging.info(armada_releases)
        else:
            raise AirflowException("Failed to retrieve Armada Releases")

    @get_pod_port_ip('maas-rack')
    def get_genesis_node_info(self, context, *args):

        # Get IP and port information of Pods from context
        k8s_pods_ip_port = context['pods_ip_port']

        # The maas-rack pod has the same IP as the genesis node
        # We will retieve that IP and return the value
        return k8s_pods_ip_port['maas-rack'].get('ip')

    def get_armada_yaml(self, context):
        # Initialize Variables
        genesis_node_ip = None

        # At this point in time, testing of the operator is being done by
        # retrieving the armada.yaml from the nginx container on the Genesis
        # node and feeding it to Armada as a string. We will assume that the
        # file name is fixed and will always be 'armada_site.yaml'. This file
        # will always be under the osh directory. This will change in the near
        # future when Armada is integrated with DeckHand.
        genesis_node_ip = context['genesis_ip']

        # Form Endpoint
        schema = 'http://'
        nginx_host_port = genesis_node_ip + ':6880'
        armada_yaml = 'osh/armada.yaml'
        design_ref = os.path.join(schema, nginx_host_port, armada_yaml)

        logging.info("Armada YAML will be retrieved from %s", design_ref)

        # TODO: We will implement the new approach when Armada and DeckHand
        # integration is completed.
        try:
            armada_manifest = requests.get(design_ref).text
        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        return armada_manifest


class ArmadaOperatorPlugin(AirflowPlugin):
    name = 'armada_operator_plugin'
    operators = [ArmadaOperator]
