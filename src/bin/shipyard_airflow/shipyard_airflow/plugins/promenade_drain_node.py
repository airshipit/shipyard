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
from airflow.exceptions import AirflowException

try:
    from promenade_base_operator import PromenadeBaseOperator
except ImportError:
    from shipyard_airflow.plugins.promenade_base_operator import \
        PromenadeBaseOperator

LOG = logging.getLogger(__name__)


class PromenadeDrainNodeOperator(PromenadeBaseOperator):

    """Promenade Drain Node Operator

    This operator will trigger promenade to drain the target
    node and ensure that the node is no longer the target of
    any pod scheduling. Promenade will evicts or deletes any
    running pod on the node.

    """

    def do_execute(self):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.

        # TODO(bryan-strassner) use:
        #     self.dc['kubernetes_provisioner.drain_timeout']
        #     self.dc['kubernetes_provisioner.drain_grace_period']

        LOG.info("Draining node...")
        time.sleep(5)

        node_drained = True

        if node_drained:
            LOG.info("Node %s has been successfully drained",
                     self.redeploy_server)
        else:
            raise AirflowException('Failed to drain %s!',
                                   self.redeploy_server)


class PromenadeDrainNodeOperatorPlugin(AirflowPlugin):

    """Creates PromenadeDrainNodeOperator in Airflow."""

    name = 'promenade_drain_node_operator'
    operators = [PromenadeDrainNodeOperator]
