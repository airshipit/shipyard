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


class PromenadeDecommissionNodeOperator(PromenadeBaseOperator):

    """Promenade Decommission Node Operator

    This operator will trigger promenade to perform steps to
    clean up the target node from the Kubernetes cluster

    """

    def do_execute(self):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        LOG.info("Decommissioning node from Kubernetes cluster...")
        time.sleep(5)

        decommission_node = True

        if decommission_node:
            LOG.info("Succesfully decommissioned node %s",
                     self.redeploy_server)
        else:
            raise AirflowException('Failed to decommission node %s!',
                                   self.redeploy_server)


class PromenadeDecommissionNodeOperatorPlugin(AirflowPlugin):

    """Creates PromenadeDecommissionNodeOperator in Airflow."""

    name = 'promenade_decommission_node_operator'
    operators = [PromenadeDecommissionNodeOperator]
