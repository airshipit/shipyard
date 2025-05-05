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

LOG = logging.getLogger(__name__)


class ArmadaGetReleasesOperator(ArmadaBaseOperator):
    """Armada Get Releases Operator

    This operator will trigger armada to get the Helm charts releases
    of the environment.

    """

    def do_execute(self, context):
        # Retrieve Armada Releases after deployment
        LOG.info("Retrieving Helm charts releases after deployment..")
        armada_get_releases = self.get_releases()

        if armada_get_releases:
            LOG.info("Successfully retrieved Helm charts releases")
            LOG.info(armada_get_releases)
        else:
            raise AirflowException("Failed to retrieve Helm charts releases!")


class ArmadaGetReleasesOperatorPlugin(AirflowPlugin):
    """Creates ArmadaGetReleasesOperator in Airflow."""

    name = 'armada_get_releases_operator'
    operators = [ArmadaGetReleasesOperator]
