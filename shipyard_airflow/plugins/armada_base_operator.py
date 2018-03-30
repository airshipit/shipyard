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
from urllib.parse import urlparse

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

import armada.common.client as client
import armada.common.session as session
from get_k8s_pod_port_ip import get_pod_port_ip
from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token
from xcom_puller import XcomPuller
from xcom_pusher import XcomPusher


class ArmadaBaseOperator(BaseOperator):

    """Armada Base Operator

    All armada related workflow operators will use the aramda
    base operator as the parent and inherit attributes and methods
    from this class

    """

    @apply_defaults
    def __init__(self,
                 armada_svc_type='armada',
                 deckhand_svc_type='deckhand',
                 main_dag_name=None,
                 query={},
                 shipyard_conf=None,
                 sub_dag_name=None,
                 svc_session=None,
                 svc_token=None,
                 xcom_push=True,
                 *args, **kwargs):
        """Initialization of ArmadaBaseOperator object.

        :param armada_svc_type: Armada Service Type
        :param deckhand_svc_type: Deckhand Service Type
        :param main_dag_name: Parent Dag
        :param query: A dictionary containing explicit query string parameters
        :param shipyard_conf: Location of shipyard.conf
        :param sub_dag_name: Child Dag
        :param svc_session: Keystone Session
        :param svc_token: Keystone Token
        :param xcom_push: xcom usage

        The Armada operator assumes that prior steps have set xcoms for
        the action and the deployment configuration

        """

        super(ArmadaBaseOperator, self).__init__(*args, **kwargs)
        self.armada_svc_type = armada_svc_type
        self.deckhand_svc_type = deckhand_svc_type
        self.main_dag_name = main_dag_name
        self.query = query
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.svc_session = svc_session
        self.svc_token = svc_token
        self.xcom_push_flag = xcom_push

    def execute(self, context):

        # Execute armada base function
        self.armada_base(context)

        # Exeute child function
        self.do_execute()

    @shipyard_service_token
    def armada_base(self, context):

        # Define task_instance
        self.task_instance = context['task_instance']

        # Set up and retrieve values from xcom
        self.xcom_puller = XcomPuller(self.main_dag_name, self.task_instance)
        self.action_info = self.xcom_puller.get_action_info()
        self.dc = self.xcom_puller.get_deployment_configuration()

        # Set up xcom_pusher to push values to xcom
        self.xcom_pusher = XcomPusher(self.task_instance)

        # Logs uuid of action performed by the Operator
        logging.info("Armada Operator for action %s", self.action_info['id'])

        # Retrieve Endpoint Information
        armada_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.armada_svc_type)

        # Set up armada client
        self.armada_client = self._init_armada_client(armada_svc_endpoint,
                                                      self.svc_token)

        # Retrieve DeckHand Endpoint Information
        deckhand_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.deckhand_svc_type)

        # Retrieve last committed revision id
        committed_revision_id = self.xcom_puller.get_design_version()

        # Get deckhand design reference url
        self.deckhand_design_ref = self._init_deckhand_design_ref(
            deckhand_svc_endpoint,
            committed_revision_id)

    @staticmethod
    def _init_armada_client(armada_svc_endpoint, svc_token):

        logging.info("Armada endpoint is %s", armada_svc_endpoint)

        # Parse Armada Service Endpoint
        armada_url = urlparse(armada_svc_endpoint)

        # Build a ArmadaSession with credentials and target host
        # information.
        logging.info("Build Armada Session")
        a_session = session.ArmadaSession(host=armada_url.hostname,
                                          port=armada_url.port,
                                          scheme='http',
                                          token=svc_token,
                                          marker=None)

        # Raise Exception if we are not able to set up the session
        if a_session:
            logging.info("Successfully Set Up Armada Session")
        else:
            raise AirflowException("Failed to set up Armada Session!")

        # Use the ArmadaSession to build a ArmadaClient that can
        # be used to make one or more API calls
        logging.info("Create Armada Client")
        _armada_client = client.ArmadaClient(a_session)

        # Raise Exception if we are not able to build armada client
        if _armada_client:
            logging.info("Successfully Set Up Armada client")

            return _armada_client
        else:
            raise AirflowException("Failed to set up Armada client!")

    @staticmethod
    def _init_deckhand_design_ref(deckhand_svc_endpoint,
                                  committed_revision_id):

        logging.info("Deckhand endpoint is %s", deckhand_svc_endpoint)

        # Form DeckHand Design Reference Path
        # This URL will be used to retrieve the Site Design YAMLs
        deckhand_path = "deckhand+" + deckhand_svc_endpoint
        _deckhand_design_ref = os.path.join(deckhand_path,
                                            "revisions",
                                            str(committed_revision_id),
                                            "rendered-documents")

        if _deckhand_design_ref:
            logging.info("Design YAMLs will be retrieved from %s",
                         _deckhand_design_ref)

            return _deckhand_design_ref
        else:
            raise AirflowException("Unable to Retrieve Design Reference!")

    @get_pod_port_ip('tiller', namespace='kube-system')
    def get_tiller_info(self, pods_ip_port={}):

        # Assign value to the 'query' dictionary so that we can pass
        # it via the Armada Client
        self.query['tiller_host'] = pods_ip_port['tiller']['ip']
        self.query['tiller_port'] = pods_ip_port['tiller']['port']


class ArmadaBaseOperatorPlugin(AirflowPlugin):

    """Creates ArmadaBaseOperator in Airflow."""

    name = 'armada_base_operator_plugin'
    operators = [ArmadaBaseOperator]
