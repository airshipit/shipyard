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


class ArmadaTestReleasesOperator(ArmadaBaseOperator):
    """Armada Test Releases Operator

    Invoke the Helm test of every deployed release or a targeted release
    specified by the "release" parameter.
    """
    def do_execute(self):
        release = self.action_params.get('release')
        if release:
            # Invoke Helm tests for specified release
            self._test_release(release)
        else:
            # Invoke Helm tests for all deployed releases
            # TODO(@drewwalters96): Support execution of tests in parallel.
            for release_list in self.get_releases().values():
                for release in release_list:
                    self._test_release(release)

    def _test_release(self, release):
        """Invoke Helm tests on a specified release

        Invokes Helm tests on a specified release using the Armada client
        and logs all test results.
        """
        LOG.info("Invoking Helm tests for release '{}'".format(release))
        try:
            armada_test_release = self.armada_client.get_test_release(
                release=release,
                timeout=None)
        except errors.ClientError as client_error:
            raise AirflowException(client_error)

        if armada_test_release:
            LOG.info("Successfully executed Helm tests for release "
                     "'{}'".format(release))
            LOG.info(armada_test_release)
        else:
            # Dump logs from Armada API pods
            self.get_k8s_logs()
            raise AirflowException("Failed to execute Helms test for "
                                   "release '{}'!".format(release))


class ArmadaTestReleasesOperatorPlugin(AirflowPlugin):
    """Creates ArmadaTestReleasesOperator in Airflow."""
    name = 'armada_test_releases_operator'
    operators = [ArmadaTestReleasesOperator]
