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
        armada_client = None
        design_ref = None

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
            svc_type = 'armada'
            context['svc_endpoint'] = ucp_service_endpoint(self,
                                                           svc_type=svc_type)
            logging.info("Armada endpoint is %s", context['svc_endpoint'])

            # Set up Armada Client
            session_client = self.armada_session_client(context)

            return session_client

        # Retrieve Deckhand Design Reference
        design_ref = self.get_deckhand_design_ref(context)

        if design_ref:
            logging.info("Design YAMLs will be retrieved from %s",
                         design_ref)
        else:
            raise AirflowException("Unable to Retrieve Design Reference!")

        # Validate Site Design
        if self.action == 'validate_site_design':
            # Initialize variable
            site_design_validity = 'invalid'

            # Retrieve Endpoint Information
            svc_type = 'armada'
            context['svc_endpoint'] = ucp_service_endpoint(self,
                                                           svc_type=svc_type)

            site_design_validity = self.armada_validate_site_design(context,
                                                                    design_ref)

            if site_design_validity == 'valid':
                logging.info("Site Design has been successfully validated")
            else:
                raise AirflowException("Site Design Validation Failed!")

            return site_design_validity

        # Retrieve armada_client via XCOM so as to perform other tasks
        armada_client = task_instance.xcom_pull(
            task_ids='create_armada_client',
            dag_id=self.main_dag_name + '.' + self.sub_dag_name)

        # Retrieve Tiller Information and assign to context 'query'
        context['query'] = self.get_tiller_info(context)

        # Armada API Call
        # Armada Status
        if self.action == 'armada_status':
            self.get_armada_status(context, armada_client)

        # Armada Apply
        elif self.action == 'armada_apply':
            self.armada_apply(context, armada_client, design_ref)

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
        a_session = session.ArmadaSession(host=armada_url.hostname,
                                          port=armada_url.port,
                                          scheme='http',
                                          token=context['svc_token'],
                                          marker=None)

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

    def armada_apply(self, context, armada_client, design_ref):
        # Initialize Variables
        armada_manifest = None
        armada_ref = design_ref
        armada_post_apply = {}
        override_values = []
        chart_set = []

        # Execute Armada Apply to install the helm charts in sequence
        logging.info("Armada Apply")
        armada_post_apply = armada_client.post_apply(manifest=armada_manifest,
                                                     manifest_ref=armada_ref,
                                                     values=override_values,
                                                     set=chart_set,
                                                     query=context['query'])

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

    def get_deckhand_design_ref(self, context):

        # Retrieve DeckHand Endpoint Information
        svc_type = 'deckhand'
        context['svc_endpoint'] = ucp_service_endpoint(self,
                                                       svc_type=svc_type)
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

        # Form Design Reference Path that we will use to retrieve
        # the Design YAMLs
        deckhand_path = "deckhand+" + context['svc_endpoint']
        deckhand_design_ref = os.path.join(deckhand_path,
                                           "revisions",
                                           str(committed_revision_id),
                                           "rendered-documents")

        return deckhand_design_ref

    @shipyard_service_token
    def armada_validate_site_design(self, context, design_ref):

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
            'href': design_ref,
            'type': "application/x-yaml"
        }

        # Requests Armada to validate site design
        logging.info("Waiting for Armada to validate site design...")

        try:
            design_validate_response = requests.post(validation_endpoint,
                                                     headers=headers,
                                                     data=json.dumps(payload))
        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        # Convert response to string
        validate_site_design = design_validate_response.text

        # Print response
        logging.info("Retrieving Armada validate site design response...")

        try:
            validate_site_design_dict = json.loads(validate_site_design)
            logging.info(validate_site_design_dict)
        except json.JSONDecodeError as e:
            raise AirflowException(e)

        # Check if site design is valid
        if validate_site_design_dict.get('status') == 'Success':
            return 'valid'
        else:
            return 'invalid'


class ArmadaOperatorPlugin(AirflowPlugin):
    name = 'armada_operator_plugin'
    operators = [ArmadaOperator]
