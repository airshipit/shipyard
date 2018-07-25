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

from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

try:
    from armada_base_operator import ArmadaBaseOperator
except ImportError:
    from shipyard_airflow.plugins.armada_base_operator import \
        ArmadaBaseOperator

from armada.exceptions import api_exceptions as errors

LOG = logging.getLogger(__name__)


class ArmadaValidateDesignOperator(ArmadaBaseOperator):

    """Armada Validate Design Operator

    This operator will trigger armada to validate the
    site design

    """

    def do_execute(self):

        # Requests Armada to validate site design
        LOG.info("Waiting for Armada to validate site design...")

        # Retrieve read timeout
        timeout = self.dc['armada.validate_design_timeout']

        # Validate Site Design
        try:
            post_validate = self.armada_client.post_validate(
                manifest=self.design_ref, timeout=timeout)

        except errors.ClientError as client_error:
            # Dump logs from Armada API pods
            self.get_k8s_logs()

            raise AirflowException(client_error)

        # Print results
        LOG.info("Retrieving Armada validate site design response...")
        LOG.info(post_validate)

        # Check if site design is valid
        status = str(post_validate.get('status', 'unspecified'))

        if status.lower() == 'success':
            LOG.info("Site Design has been successfully validated")
        else:
            # Dump logs from Armada API pods
            self.get_k8s_logs()

            raise AirflowException("Site Design Validation Failed "
                                   "with status: {}!".format(status))


class ArmadaValidateDesignOperatorPlugin(AirflowPlugin):

    """Creates ArmadaValidateDesignOperator in Airflow."""

    name = 'armada_validate_design_operator'
    operators = [ArmadaValidateDesignOperator]
