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

from drydock_base_operator import DrydockBaseOperator


class DrydockDestroyNodeOperator(DrydockBaseOperator):

    """Drydock Destroy Node Operator

    This operator will trigger drydock to destroy a bare metal
    node

    """

    def do_execute(self):

        # Retrieve query interval and timeout
        q_interval = self.dc['physical_provisioner.destroy_interval']
        task_timeout = self.dc['physical_provisioner.destroy_timeout']

        # NOTE: This is a PlaceHolder function. The 'destroy_node'
        # functionalities in DryDock is being worked on and is not
        # ready at the moment.
        logging.info("Destroying node %s from cluster...",
                     self.redeploy_server)
        time.sleep(15)
        logging.info("Successfully deleted node %s", self.redeploy_server)


class DrydockDestroyNodeOperatorPlugin(AirflowPlugin):

    """Creates DrydockDestroyNodeOperator in Airflow."""

    name = 'drydock_destroy_node_operator'
    operators = [DrydockDestroyNodeOperator]
