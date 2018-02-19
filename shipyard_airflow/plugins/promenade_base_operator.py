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

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token
from xcom_puller import XcomPuller


class PromenadeBaseOperator(BaseOperator):

    """Promenade Base Operator

    All promenade related workflow operators will use the promenade
    base operator as the parent and inherit attributes and methods
    from this class
    """

    @apply_defaults
    def __init__(self,
                 main_dag_name=None,
                 promenade_svc_endpoint=None,
                 promenade_svc_type='kubernetesprovisioner',
                 redeploy_server=None,
                 shipyard_conf=None,
                 sub_dag_name=None,
                 svc_token=None,
                 xcom_push=True,
                 *args, **kwargs):
        """Initialization of PromenadeBaseOperator object.

        :param main_dag_name: Parent Dag
        :param promenade_svc_endpoint: Promenade Service Endpoint
        :param promenade_svc_type: Promenade Service Type
        :param redeploy_server: Server to be redeployed
        :param shipyard_conf: Path of shipyard.conf
        :param sub_dag_name: Child Dag
        :param svc_token: Keystone Token
        :param xcom_push: xcom usage
        The Drydock operator assumes that prior steps have set xcoms for
        the action and the deployment configuration
        """

        super(PromenadeBaseOperator, self).__init__(*args,
                                                    **kwargs)
        self.main_dag_name = main_dag_name
        self.promenade_svc_endpoint = promenade_svc_endpoint
        self.promenade_svc_type = promenade_svc_type
        self.redeploy_server = redeploy_server
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.svc_token = svc_token
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        # Execute promenade base function
        self.promenade_base(context)

        # Exeute child function
        self.do_execute()

    @shipyard_service_token
    def promenade_base(self, context):
        # Define task_instance
        task_instance = context['task_instance']

        # Set up and retrieve values from xcom
        self.xcom_puller = XcomPuller(self.main_dag_name, task_instance)
        self.action_info = self.xcom_puller.get_action_info()
        self.dc = self.xcom_puller.get_deployment_configuration()

        # Logs uuid of Shipyard action
        logging.info("Executing Shipyard Action %s", self.action_info['id'])

        # Retrieve information of the server that we want to redeploy
        # if user executes the 'redeploy_server' dag
        if self.action_info['dag_id'] == 'redeploy_server':
            self.redeploy_server = self.action_info['parameters'].get(
                'server-name')

            if self.redeploy_server:
                logging.info("Server to be redeployed is %s",
                             self.redeploy_server)
            else:
                raise AirflowException('%s was unable to retrieve the '
                                       'server to be redeployed.'
                                       % self.__class__.__name__)

        # Retrieve promenade endpoint
        self.promenade_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.promenade_svc_type)

        logging.info("Promenade endpoint is %s",
                     self.promenade_svc_endpoint)


class PromenadeBaseOperatorPlugin(AirflowPlugin):

    """Creates PromenadeBaseOperator in Airflow."""

    name = 'promenade_base_operator_plugin'
    operators = [PromenadeBaseOperator]
