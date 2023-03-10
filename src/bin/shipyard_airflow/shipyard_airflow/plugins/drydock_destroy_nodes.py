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
"""Invoke the Drydock steps for destroying a node."""
import logging

from airflow.exceptions import AirflowException
from airflow.plugins_manager import AirflowPlugin

try:
    from drydock_base_operator import DrydockBaseOperator
    from drydock_base_operator import gen_node_name_filter
    from drydock_errors import (
        DrydockTaskFailedException,
        DrydockTaskTimeoutException
    )
except ImportError:
    from shipyard_airflow.plugins.drydock_base_operator import \
        DrydockBaseOperator
    from shipyard_airflow.plugins.drydock_base_operator import \
        gen_node_name_filter
    from shipyard_airflow.plugins.drydock_errors import (
        DrydockTaskFailedException,
        DrydockTaskTimeoutException
    )

LOG = logging.getLogger(__name__)


class DrydockDestroyNodeOperator(DrydockBaseOperator):
    """Drydock Destroy Node Operator

    This operator will trigger drydock to destroy a bare metal
    node
    """
    def do_execute(self):
        self.successes = []

        LOG.info("Destroying nodes [%s]", ", ".join(self.target_nodes))
        self.setup_configured_values()
        self.node_filter = gen_node_name_filter(self.target_nodes)
        self.execute_destroy()
        self.successes = self.get_successes_for_task(self.drydock_task_id)
        self.report_summary()
        if not self.is_destroy_successful():
            raise AirflowException(
                "One or more nodes requested for destruction failed to destroy"
            )

    def setup_configured_values(self):
        """Retrieve and localize the interval and timeout values for destroy
        """
        self.dest_interval = self.dc['physical_provisioner.destroy_interval']
        self.dest_timeout = self.dc['physical_provisioner.destroy_timeout']

    def execute_destroy(self):
        """Run the task to destroy the nodes specified in the node_filter

        :param node_filter: The Drydock node filter with the nodes to destroy
        """
        task_name = 'destroy_nodes'
        self.create_task(task_name)

        try:
            self.query_task(self.dest_interval, self.dest_timeout)
        except DrydockTaskFailedException:
            LOG.exception("Task %s has failed. Some nodes may have been "
                          "destroyed. The report at the end of processing "
                          "this step contains the results", task_name)
        except DrydockTaskTimeoutException:
            LOG.warning("Task %s has timed out after %s seconds. "
                        "Some nodes may "
                        "have been destroyed. The report at the end of "
                        "processing this step contains the results", task_name,
                        self.dest_timeout)

    def report_summary(self):
        """Reports the successfully destroyed nodes"""
        failed = list(set(self.target_nodes) - set(self.successes))
        LOG.info("=====   Destroy Nodes Summary   =====")
        LOG.info("  Nodes requested: %s", ", ".join(sorted(self.target_nodes)))
        LOG.info("  Nodes destroyed: %s ", ", ".join(sorted(self.successes)))
        LOG.info("  Nodes not destroyed: %s", ", ".join(sorted(failed)))
        LOG.info("===== End Destroy Nodes Summary =====")

    def is_destroy_successful(self):
        """Boolean if the destroy nodes was completely succesful."""
        failed = set(self.target_nodes) - set(self.successes)
        return not failed


class DrydockDestroyNodeOperatorPlugin(AirflowPlugin):

    """Creates DrydockDestroyNodeOperator in Airflow."""

    name = 'drydock_destroy_node_operator'
    operators = [DrydockDestroyNodeOperator]
