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


class PromenadeClearLabelsOperator(PromenadeBaseOperator):

    """Promenade Clear Labels Operator

    This operator will trigger promenade to clear the labels on
    the target node

    """

    def do_execute(self):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.

        # TODO(bryan-strassner) use:
        #     self.dc['kubernetes_provisioner.clear_labels_timeout']

        logging.info("Removing labels on node...")
        time.sleep(5)

        labels_removed = True

        if labels_removed:
            logging.info("Successfully removed labels on %s",
                         self.redeploy_server)
        else:
            raise AirflowException('Failed to remove labels on %s!',
                                   self.redeploy_server)


class PromenadeClearLabelsOperatorPlugin(AirflowPlugin):

    """Creates PromenadeClearLabelsOperator in Airflow."""

    name = 'promenade_clear_labels_operator'
    operators = [PromenadeClearLabelsOperator]
