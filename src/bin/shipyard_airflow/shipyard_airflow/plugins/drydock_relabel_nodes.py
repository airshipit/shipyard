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
"""Update node labels using Drydock
"""
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


class DrydockRelabelNodesOperator(DrydockBaseOperator):
    """Drydock Relabel Nodes Operator

    Update Kubernetes node labels on a targeted set of nodes
    using Drydock.
    """

    def do_execute(self):
        self.successes = []

        LOG.info("Relabeling nodes [%s]", ", ".join(self.target_nodes))
        self.setup_configured_values()
        self.node_filter = gen_node_name_filter(self.target_nodes)
        self.execute_relabel()
        self.successes = self.get_successes_for_task(self.drydock_task_id)
        self.report_summary()
        if not self.is_task_successful():
            raise AirflowException(
                "One or more nodes requested for relabeling failed to relabel"
            )

    def setup_configured_values(self):
        """Retrieve and localize the interval and timeout values for destroy
        """
        self.q_interval = \
            self.dc['physical_provisioner.relabel_nodes_interval']
        self.task_timeout = \
            self.dc['physical_provisioner.relabel_nodes_timeout']

    def execute_relabel(self):
        # Trigger DryDock to execute task
        task_name = 'relabel_nodes'

        self.create_task(task_name)

        # Query Task
        try:
            self.query_task(self.q_interval, self.task_timeout)
        except DrydockTaskFailedException:
            LOG.exception("Task %s has failed. Some nodes may have been "
                          "relabeled. The report at the end of processing "
                          "this step contains the results", task_name)
        except DrydockTaskTimeoutException:
            LOG.warn("Task %s has timed out after %s seconds. Some nodes may "
                     "have been relabeled. The report at the end of "
                     "processing this step contains the results", task_name,
                     self.task_timeout)

    def report_summary(self):
        """Reports the successfully relabeled nodes"""
        failed = list(set(self.target_nodes) - set(self.successes))
        LOG.info("=====   Relabel Nodes Summary   =====")
        LOG.info("  Nodes requested: %s", ", ".join(sorted(self.target_nodes)))
        LOG.info("  Nodes relabeled: %s ", ", ".join(sorted(self.successes)))
        LOG.info("  Nodes not relabeled: %s", ", ".join(sorted(failed)))
        LOG.info("===== End Relabel Nodes Summary =====")

    # TODO: redundant with drydock_destroy_nodes...worth refactoring?
    def is_task_successful(self):
        """Boolean if the task was completely succesful."""
        failed = set(self.target_nodes) - set(self.successes)
        return not failed


class DrydockRelabelNodesOperatorPlugin(AirflowPlugin):

    """Creates DrydockRelabelNodesOperator in Airflow."""

    name = 'drydock_relabel_nodes_operator'
    operators = [DrydockRelabelNodesOperator]
