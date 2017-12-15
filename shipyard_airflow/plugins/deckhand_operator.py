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
import yaml

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

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
                 workflow_info={},
                 xcom_push=True,
                 *args, **kwargs):

        super(DeckhandOperator, self).__init__(*args, **kwargs)
        self.action = action
        self.main_dag_name = main_dag_name
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.workflow_info = workflow_info
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        # Initialize Variables
        context['svc_type'] = 'deckhand'
        deckhand_design_version = None

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

        # Retrieve Endpoint Information
        context['svc_endpoint'] = ucp_service_endpoint(self, context)
        logging.info("Deckhand endpoint is %s", context['svc_endpoint'])

        # Deckhand API Call
        # Retrieve Design Version from DeckHand
        if self.action == 'deckhand_get_design_version':
            # Retrieve DeckHand Design Version
            deckhand_design_version = self.deckhand_get_design(context)

            if deckhand_design_version:
                return deckhand_design_version
            else:
                raise AirflowException('Failed to retrieve revision ID!')

        # Validate Design using DeckHand
        elif self.action == 'deckhand_validate_site_design':
            # Retrieve revision_id from xcom
            # Note that in the case of 'deploy_site', the dag_id will
            # be 'deploy_site.deckhand_get_design_version' for the
            # 'deckhand_get_design_version' task. We need to extract
            # the xcom value from it in order to get the value of the
            # last committed revision ID
            context['revision_id'] = task_instance.xcom_pull(
                task_ids='deckhand_get_design_version',
                dag_id=self.main_dag_name + '.deckhand_get_design_version')

            logging.info("Revision ID is %d", context['revision_id'])
            self.deckhand_validate_site(context)

        # No action to perform
        else:
            logging.info('No Action to Perform')

    @shipyard_service_token
    def deckhand_get_design(self, context):
        # Retrieve Keystone Token and assign to X-Auth-Token Header
        x_auth_token = {"X-Auth-Token": context['svc_token']}

        # Form Revision Endpoint
        revision_endpoint = os.path.join(context['svc_endpoint'],
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
    def deckhand_validate_site(self, context):
        # Retrieve Keystone Token and assign to X-Auth-Token Header
        x_auth_token = {"X-Auth-Token": context['svc_token']}

        # Form Validation Endpoint
        validation_endpoint = os.path.join(context['svc_endpoint'],
                                           'revisions',
                                           str(context['revision_id']),
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
                         context['revision_id'])
        else:
            raise AirflowException("DeckHand Site Design Validation Failed!")


class DeckhandOperatorPlugin(AirflowPlugin):
    name = 'deckhand_operator_plugin'
    operators = [DeckhandOperator]
