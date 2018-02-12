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

from promenade_base_operator import PromenadeBaseOperator


class PromenadeShutdownKubeletOperator(PromenadeBaseOperator):

    """Promenade Shutdown Kubelet Operator

    This operator will trigger promenade to shut down kubelet
    on the target node.

    """

    def do_execute(self):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.
        logging.info("Shutting down kubelet on node...")
        time.sleep(5)

        shutdown_kubelet = True

        if shutdown_kubelet:
            logging.info("Successfully shut down kubelet on %s",
                         self.redeploy_server)
        else:
            raise AirflowException('Failed to shut down kubelet on %s!',
                                   self.redeploy_server)


class PromenadeShutdownKubeletOperatorPlugin(AirflowPlugin):

    """Creates PromenadeShutdownKubeletOperator in Airflow."""

    name = 'promenade_shutdown_kubelet_operator'
    operators = [PromenadeShutdownKubeletOperator]
