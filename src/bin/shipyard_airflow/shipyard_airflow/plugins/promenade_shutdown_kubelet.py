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


class PromenadeShutdownKubeletOperator(PromenadeBaseOperator):
    """Promenade Shutdown Kubelet Operator

    This operator will trigger promenade to shut down kubelet
    on the target node.

    """

    def do_execute(self, context):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        LOG.info("Shutting down kubelet on node...")
        time.sleep(5)

        shutdown_kubelet = True

        if shutdown_kubelet:
            LOG.info("Successfully shut down kubelet on %s",
                     self.redeploy_server)
        else:
            raise AirflowException('Failed to shut down kubelet on %s!',
                                   self.redeploy_server)


class PromenadeShutdownKubeletOperatorPlugin(AirflowPlugin):
    """Creates PromenadeShutdownKubeletOperator in Airflow."""

    name = 'promenade_shutdown_kubelet_operator'
    operators = [PromenadeShutdownKubeletOperator]
