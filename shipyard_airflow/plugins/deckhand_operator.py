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
import logging
import os
import requests
import yaml

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException
from keystoneauth1.identity import v3 as keystone_v3
from keystoneauth1 import session as keystone_session

from deckhand.client import client as deckhand_client
from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token


class DeckhandOperator(BaseOperator):
    """
    Supports interaction with Deckhand
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
                 svc_token=None,
                 workflow_info={},
                 xcom_push=True,
                 *args, **kwargs):

        super(DeckhandOperator, self).__init__(*args, **kwargs)
        self.action = action
        self.main_dag_name = main_dag_name
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.svc_token = svc_token
        self.workflow_info = workflow_info
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        # Initialize Variables
        deckhand_design_version = None
        redeploy_server = None
        revision_id = None

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
        logging.info("DeckHand Operator for action %s", workflow_info['id'])

        # Retrieve information of the server that we want to redeploy if user
        # executes the 'redeploy_server' dag
        if workflow_info['dag_id'] == 'redeploy_server':
            redeploy_server = workflow_info['parameters'].get('server-name')

            if redeploy_server:
                logging.info("Server to be redeployed is %s", redeploy_server)
            else:
                raise AirflowException('Unable to retrieve information of '
                                       'node to be redeployed!')

        # Retrieve Endpoint Information
        svc_type = 'deckhand'
        deckhand_svc_endpoint = ucp_service_endpoint(self,
                                                     svc_type=svc_type)
        logging.info("Deckhand endpoint is %s", deckhand_svc_endpoint)

        # Deckhand API Call
        # Retrieve Design Version from DeckHand
        if self.action == 'deckhand_get_design_version':
            # Retrieve DeckHand Design Version
            deckhand_design_version = self.deckhand_get_design(
                deckhand_svc_endpoint)

            if deckhand_design_version:
                return deckhand_design_version
            else:
                raise AirflowException('Failed to retrieve revision ID!')

        # Retrieve revision_id from xcom
        # Note that in the case of 'deploy_site', the dag_id will
        # be 'deploy_site.deckhand_get_design_version' for the
        # 'deckhand_get_design_version' task. We need to extract
        # the xcom value from it in order to get the value of the
        # last committed revision ID
        revision_id = task_instance.xcom_pull(
            task_ids='deckhand_get_design_version',
            dag_id=self.main_dag_name + '.deckhand_get_design_version')

        logging.info("Revision ID is %d", revision_id)

        # Retrieve Rendered Document from DeckHand
        if self.action == 'shipyard_retrieve_rendered_doc':
            if revision_id:
                self.retrieve_rendered_doc(context,
                                           revision_id)
            else:
                raise AirflowException('Invalid revision ID!')

        # Validate Design using DeckHand
        elif self.action == 'deckhand_validate_site_design':
            if revision_id:
                self.deckhand_validate_site(context,
                                            revision_id)
            else:
                raise AirflowException('Invalid revision ID!')

        # No action to perform
        else:
            logging.info('No Action to Perform')

    @shipyard_service_token
    def deckhand_get_design(self, deckhand_svc_endpoint):
        # Retrieve Keystone Token and assign to X-Auth-Token Header
        x_auth_token = {"X-Auth-Token": self.svc_token}

        # Form Revision Endpoint
        revision_endpoint = os.path.join(deckhand_svc_endpoint,
                                         'revisions')

        # Retrieve Revision
        logging.info("Retrieving revisions information...")

        try:
            query_params = {'tag': 'committed', 'sort': 'id', 'order': 'desc'}
            revisions = yaml.safe_load(requests.get(
                revision_endpoint, headers=x_auth_token,
                params=query_params, timeout=30).text)
        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        logging.info(revisions)

        # Print the number of revisions that is currently available on
        # DeckHand
        logging.info("The number of revisions is %s", revisions['count'])

        # Initialize Committed Version
        committed_ver = None

        # Search for the last committed version and save it as xcom
        revision_list = revisions.get('results', [])
        if revision_list:
            committed_ver = revision_list[-1].get('id')

        if committed_ver:
            logging.info("Last committed revision is %d", committed_ver)
            return committed_ver
        else:
            raise AirflowException("Failed to retrieve committed revision!")

    @shipyard_service_token
    def deckhand_validate_site(self, deckhand_svc_endpoint, revision_id):
        # Retrieve Keystone Token and assign to X-Auth-Token Header
        x_auth_token = {"X-Auth-Token": self.svc_token}

        # Form Validation Endpoint
        validation_endpoint = os.path.join(deckhand_svc_endpoint,
                                           'revisions',
                                           str(revision_id),
                                           'validations')
        logging.info(validation_endpoint)

        # Retrieve Validation list
        logging.info("Retrieving validation list...")

        try:
            retrieved_list = yaml.safe_load(
                requests.get(validation_endpoint, headers=x_auth_token,
                             timeout=30).text)
        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        logging.info(retrieved_list)

        # Initialize Validation Status
        validation_status = True

        # Construct validation_list
        validation_list = retrieved_list.get('results', [])

        # Assigns 'False' to validation_status if result status
        # is 'failure'
        for validation in validation_list:
            if validation.get('status') == 'failure':
                validation_status = False
                break

        if validation_status:
            logging.info("Revision %d has been successfully validated",
                         revision_id)
        else:
            raise AirflowException("DeckHand Site Design Validation Failed!")

    def retrieve_rendered_doc(self, context, revision_id):

        # Initialize Variables
        auth = None
        keystone_auth = {}
        rendered_doc = []
        sess = None

        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        # Construct Session Argument
        for attr in ('auth_url', 'password', 'project_domain_name',
                     'project_name', 'username', 'user_domain_name'):
            keystone_auth[attr] = config.get('keystone_authtoken', attr)

        # Set up keystone session
        auth = keystone_v3.Password(**keystone_auth)
        sess = keystone_session.Session(auth=auth)

        logging.info("Setting up DeckHand Client...")

        # Set up DeckHand Client
        # NOTE: The communication between the Airflow workers and Deckhand
        # happens via the 'internal' endpoint and not the 'public' endpoint.
        # Hence we will need to override the 'endpoint_type' from the default
        # 'public' endpoint to 'internal' endpoint.
        deckhandclient = deckhand_client.Client(session=sess,
                                                endpoint_type='internal')

        logging.info("Retrieving Rendered Document...")

        # Retrieve Rendered Document
        try:
            rendered_doc = deckhandclient.revisions.documents(revision_id,
                                                              rendered=True)

            logging.info("Successfully Retrieved Rendered Document")
            logging.info(rendered_doc)

        except:
            raise AirflowException("Failed to Retrieve Rendered Document!")


class DeckhandOperatorPlugin(AirflowPlugin):
    name = 'deckhand_operator_plugin'
    operators = [DeckhandOperator]
