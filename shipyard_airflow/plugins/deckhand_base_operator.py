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

import configparser
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

from deckhand.client import client as deckhand_client
from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token


class DeckhandBaseOperator(BaseOperator):

    """Deckhand Base Operator

    All deckhand related workflow operators will use the deckhand
    base operator as the parent and inherit attributes and methods
    from this class

    """

    @apply_defaults
    def __init__(self,
                 committed_ver=None,
                 deckhandclient=None,
                 deckhand_client_read_timeout=None,
                 deckhand_svc_endpoint=None,
                 deckhand_svc_type='deckhand',
                 main_dag_name=None,
                 revision_id=None,
                 shipyard_conf=None,
                 sub_dag_name=None,
                 svc_session=None,
                 svc_token=None,
                 validation_read_timeout=None,
                 workflow_info={},
                 xcom_push=True,
                 *args, **kwargs):
        """Initialization of DeckhandBaseOperator object.

        :param committed_ver: Last committed version
        :param deckhandclient: An instance of deckhand client
        :param deckhand_client_read_timeout: Deckhand client connect timeout
        :param deckhand_svc_endpoint: Deckhand Service Endpoint
        :param deckhand_svc_type: Deckhand Service Type
        :param main_dag_name: Parent Dag
        :param revision_id: Target revision for workflow
        :param shipyard_conf: Path of shipyard.conf
        :param sub_dag_name: Child Dag
        :param svc_session: Keystone Session
        :param svc_token: Keystone Token
        :param validation_read_timeout: Deckhand validation timeout
        :param workflow_info: Information related to current workflow
        :param xcom_push: xcom usage

        """

        super(DeckhandBaseOperator, self).__init__(*args, **kwargs)
        self.committed_ver = committed_ver
        self.deckhandclient = deckhandclient
        self.deckhand_client_read_timeout = deckhand_client_read_timeout
        self.deckhand_svc_endpoint = deckhand_svc_endpoint
        self.deckhand_svc_type = deckhand_svc_type
        self.main_dag_name = main_dag_name
        self.revision_id = revision_id
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.svc_session = svc_session
        self.svc_token = svc_token
        self.validation_read_timeout = validation_read_timeout
        self.workflow_info = workflow_info
        self.xcom_push_flag = xcom_push

    def execute(self, context):

        # Execute deckhand base function
        self.deckhand_base(context)

        # Exeute child function
        self.do_execute()

        # Push last committed version to xcom for the
        # 'deckhand_get_design_version' subdag
        if self.sub_dag_name == 'deckhand_get_design_version':
            return self.committed_ver

    @shipyard_service_token
    def deckhand_base(self, context):

        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        # Initialize variables
        self.deckhand_client_read_timeout = int(config.get(
            'requests_config', 'deckhand_client_read_timeout'))

        self.validation_read_timeout = int(config.get(
            'requests_config', 'validation_read_timeout'))

        # Define task_instance
        task_instance = context['task_instance']

        # Extract information related to current workflow
        # The workflow_info variable will be a dictionary
        # that contains information about the workflow such
        # as action_id, name and other related parameters
        self.workflow_info = task_instance.xcom_pull(
            task_ids='action_xcom', key='action',
            dag_id=self.main_dag_name)

        # Logs uuid of Shipyard action
        logging.info("Executing Shipyard Action %s",
                     self.workflow_info['id'])

        # Retrieve Endpoint Information
        self.deckhand_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.deckhand_svc_type)

        logging.info("Deckhand endpoint is %s",
                     self.deckhand_svc_endpoint)

        # Set up DeckHand Client
        logging.info("Setting up DeckHand Client...")

        # NOTE: The communication between the Airflow workers
        # and Deckhand happens via the 'internal' endpoint.
        self.deckhandclient = deckhand_client.Client(
            session=self.svc_session, endpoint_type='internal')

        if not self.deckhandclient:
            raise AirflowException('Failed to set up deckhand client!')

        # Retrieve 'revision_id' from xcom for tasks other than
        # 'deckhand_get_design_version'
        #
        # NOTE: In the case of 'deploy_site', the dag_id will
        # be 'deploy_site.deckhand_get_design_version' for the
        # 'deckhand_get_design_version' task. We need to extract
        # the xcom value from it in order to get the value of the
        # last committed revision ID
        if self.sub_dag_name != 'deckhand_get_design_version':

            # Retrieve 'revision_id' from xcom
            self.revision_id = task_instance.xcom_pull(
                task_ids='deckhand_get_design_version',
                dag_id=self.main_dag_name + '.deckhand_get_design_version')

            if self.revision_id:
                logging.info("Revision ID is %d", self.revision_id)
            else:
                raise AirflowException('Failed to retrieve Revision ID!')


class DeckhandBaseOperatorPlugin(AirflowPlugin):

    """Creates DeckhandBaseOperator in Airflow."""

    name = 'deckhand_base_operator_plugin'
