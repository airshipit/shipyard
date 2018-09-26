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

from airflow.exceptions import AirflowException
from airflow.plugins_manager import AirflowPlugin

try:
    from armada_base_operator import ArmadaBaseOperator
except ImportError:
    from shipyard_airflow.plugins.armada_base_operator import \
        ArmadaBaseOperator
from armada.exceptions import api_exceptions as errors

LOG = logging.getLogger(__name__)


class ArmadaGetStatusOperator(ArmadaBaseOperator):

    """Armada Get Status Operator

    This operator will trigger armada to get the current status of
    Tiller. Tiller needs to be in a healthy state before any site
    deployment/update.

    """

    def do_execute(self):

        # Retrieve Tiller Information
        self.get_tiller_info(pods_ip_port={})

        # Retrieve read timeout
        timeout = self.dc['armada.get_status_timeout']

        # Check State of Tiller
        try:
            armada_get_status = self.armada_client.get_status(
                self.query,
                timeout=timeout)

        except errors.ClientError as client_error:
            raise AirflowException(client_error)

        # Tiller State will return boolean value, i.e. True/False
        # Raise Exception if Tiller is unhealthy
        if armada_get_status['tiller']['state']:
            LOG.info("Tiller is in running state")
            LOG.info("Tiller version is %s",
                     armada_get_status['tiller']['version'])

        else:
            raise AirflowException("Please check Tiller!")


class ArmadaGetStatusOperatorPlugin(AirflowPlugin):

    """Creates ArmadaGetStatusOperator in Airflow."""

    name = 'armada_get_status_operator'
    operators = [ArmadaGetStatusOperator]
