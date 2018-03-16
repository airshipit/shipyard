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

from airflow.plugins_manager import AirflowPlugin

from check_k8s_node_status import check_node_status
from drydock_base_operator import DrydockBaseOperator


class DrydockDeployNodesOperator(DrydockBaseOperator):

    """Drydock Deploy Nodes Operator

    This operator will trigger drydock to deploy the bare metal
    nodes

    """

    def do_execute(self):

        # Trigger DryDock to execute task
        self.create_task('deploy_nodes')

        # Retrieve query interval and timeout
        q_interval = self.dc['physical_provisioner.deploy_interval']
        task_timeout = self.dc['physical_provisioner.deploy_timeout']

        # Query Task
        self.query_task(q_interval, task_timeout)

        # It takes time for the cluster join process to be triggered across
        # all the nodes in the cluster. Hence there is a need to back off
        # and wait before checking the state of the cluster join process.
        join_wait = self.dc['physical_provisioner.join_wait']

        logging.info("All nodes deployed in MAAS")
        logging.info("Wait for %d seconds before checking node state...",
                     join_wait)

        time.sleep(join_wait)

        # Check that cluster join process is completed before declaring
        # deploy_node as 'completed'.
        node_st_timeout = self.dc['kubernetes.node_status_timeout']
        node_st_interval = self.dc['kubernetes.node_status_interval']

        check_node_status(node_st_timeout, node_st_interval)


class DrydockDeployNodesOperatorPlugin(AirflowPlugin):

    """Creates DrydockDeployNodesOperator in Airflow."""

    name = 'drydock_deploy_nodes_operator'
    operators = [DrydockDeployNodesOperator]
