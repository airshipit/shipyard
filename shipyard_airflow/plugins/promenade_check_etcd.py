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

LOG = logging.getLogger(__name__)


class PromenadeCheckEtcdOperator(PromenadeBaseOperator):

    """Promenade Check ETCD Operator

    This operator will trigger promenade to retrieve the current
    state of etcd.

    """

    def do_execute(self):
        # Placeholder function. Updates will be made when the Promenade
        # API is ready for consumption.

        # TODO(bryan-strassner) use:
        #     self.dc['kubernetes_provisioner.etcd_ready_timeout']
        #     self.dc['kubernetes_provisioner.remove_etcd_timeout']
        LOG.info("Performing health check on etcd...")
        time.sleep(5)

        check_etcd = True

        if check_etcd:
            LOG.info("The etcd cluster is healthy and ready")
        else:
            raise AirflowException('Please check the state of etcd!')


class PromenadeCheckEtcdOperatorPlugin(AirflowPlugin):

    """Creates PromenadeCheckEtcdOperator in Airflow."""

    name = 'promenade_check_etcd_operator'
    operators = [PromenadeCheckEtcdOperator]
