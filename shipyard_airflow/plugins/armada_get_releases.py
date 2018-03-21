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

from armada_base_operator import ArmadaBaseOperator
from armada.exceptions import api_exceptions as errors


class ArmadaGetReleasesOperator(ArmadaBaseOperator):

    """Armada Get Releases Operator

    This operator will trigger armada to get the Helm charts releases
    of the environment.

    """

    def do_execute(self):

        # Retrieve Tiller Information
        self.get_tiller_info(pods_ip_port={})

        # Retrieve read timeout
        timeout = self.dc['armada.get_releases_timeout']

        # Retrieve Armada Releases after deployment
        logging.info("Retrieving Helm charts releases after deployment..")

        try:
            armada_get_releases = self.armada_client.get_releases(
                self.query,
                timeout=timeout)

        except errors.ClientError as client_error:
            raise AirflowException(client_error)

        if armada_get_releases:
            logging.info("Successfully retrieved Helm charts releases")
            logging.info(armada_get_releases)
        else:
            raise AirflowException("Failed to retrieve Helm charts releases!")


class ArmadaGetReleasesOperatorPlugin(AirflowPlugin):

    """Creates ArmadaGetReleasesOperator in Airflow."""

    name = 'armada_get_releases_operator'
    operators = [ArmadaGetReleasesOperator]
