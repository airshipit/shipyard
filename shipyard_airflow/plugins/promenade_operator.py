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
import time

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

from service_endpoint import ucp_service_endpoint
from service_token import shipyard_service_token


class PromenadeOperator(BaseOperator):
    """
    Supports interaction with Promenade
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

        super(PromenadeOperator, self).__init__(*args, **kwargs)
        self.action = action
        self.main_dag_name = main_dag_name
        self.shipyard_conf = shipyard_conf
        self.sub_dag_name = sub_dag_name
        self.svc_token = svc_token
        self.workflow_info = workflow_info
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        # Initialize Variables
        check_etcd = False
        delete_node = False
        labels_removed = False
        node_drained = False
        redeploy_server = None
        stop_kubelet = False

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
        logging.info("Promenade Operator for action %s", workflow_info['id'])

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
        svc_type = 'kubernetesprovisioner'
        context['svc_endpoint'] = ucp_service_endpoint(self,
                                                       svc_type=svc_type)
        logging.info("Promenade endpoint is %s", context['svc_endpoint'])

        # Promenade API Call
        # Drain node using Promenade
        if self.action == 'promenade_drain_node':
            node_drained = self.promenade_drain_node(redeploy_server)

            if node_drained:
                logging.info("Node %s has been successfully drained",
                             redeploy_server)
            else:
                raise AirflowException('Failed to drain %s!',
                                       redeploy_server)

        # Remove labels using Promenade
        elif self.action == 'promenade_remove_labels':
            labels_removed = self.promenade_remove_labels(redeploy_server)

            if labels_removed:
                logging.info("Successfully removed labels on %s",
                             redeploy_server)
            else:
                raise AirflowException('Failed to remove labels on %s!',
                                       redeploy_server)

        # Stops kubelet on node using Promenade
        elif self.action == 'promenade_stop_kubelet':
            stop_kubelet = self.promenade_stop_kubelet(redeploy_server)

            if stop_kubelet:
                logging.info("Successfully stopped kubelet on %s",
                             redeploy_server)
            else:
                raise AirflowException('Failed to stopped kubelet on %s!',
                                       redeploy_server)

        # Performs etcd sanity check using Promenade
        elif self.action == 'promenade_check_etcd':
            check_etcd = self.promenade_check_etcd()

            if check_etcd:
                logging.info("The etcd cluster is healthy and ready")
            else:
                raise AirflowException('Please check the state of etcd!')

        # Delete node from cluster using Promenade
        elif self.action == 'promenade_delete_node':
            delete_node = self.promenade_delete_node(redeploy_server)

            if delete_node:
                logging.info("Succesfully deleted node %s from cluster",
                             redeploy_server)
            else:
                raise AirflowException('Failed to node %s from cluster!',
                                       redeploy_server)

        # No action to perform
        else:
            logging.info('No Action to Perform')

    @shipyard_service_token
    def promenade_drain_node(self, redeploy_server):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        logging.info("The token is %s", self.svc_token)
        logging.info("Draining node...")
        time.sleep(15)

        return True

    @shipyard_service_token
    def promenade_remove_labels(self, redeploy_server):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        logging.info("Removing labels on node...")
        time.sleep(15)

        return True

    @shipyard_service_token
    def promenade_stop_kubelet(self, redeploy_server):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        logging.info("Stopping kubelet on node...")
        time.sleep(15)

        return True

    @shipyard_service_token
    def promenade_check_etcd(self):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        logging.info("Performing health check on etcd...")
        time.sleep(15)

        return True

    @shipyard_service_token
    def promenade_delete_node(self, redeploy_server):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        logging.info("Deleting node from cluster...")
        time.sleep(15)

        return True


class PromenadeOperatorPlugin(AirflowPlugin):
    name = 'promenade_operator_plugin'
    operators = [PromenadeOperator]
