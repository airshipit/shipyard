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
    from drydock_base_operator import DrydockBaseOperator
except ImportError:
    from shipyard_airflow.plugins.drydock_base_operator import \
        DrydockBaseOperator

LOG = logging.getLogger(__name__)
safeguard_message_header = (
    "No nodes were found by Drydock. Safeguard triggered to prevent "
    "continued deployment of nodes.")
safeguard_message_body = (
    "This condition can occur if update_site is invoked before a deploy_site "
    "has previously deployed nodes in this site. If nodes are expected to be "
    "present (previously deployed), this is a serious condition and should "
    "be investigated. This behavior can be bypassed by setting "
    "continue-on-fail to true.")
safeguard_bypassed_message = (
    "Nodes do not exist, but continue-on-fail is True. Safeguard bypassed by "
    "invocation options.")


class DrydockVerifyNodesExistOperator(DrydockBaseOperator):
    """Drydock Verify nodes exist Operator

    Check that ANY nodes exist.
    One use of this is to prevent an update_site from redeploying servers if
    the underlying datastores have lost their data. Doing this prevents
    destruction of potentially running workloads.
    """

    def do_execute(self, context):
        LOG.info("Verifying that nodes exist before proceeding.")
        node_list = self.get_nodes()
        if not node_list:
            if self.continue_on_fail():
                LOG.info(safeguard_bypassed_message)
            else:
                LOG.error(safeguard_message_header)
                LOG.error(safeguard_message_body)
                raise AirflowException(safeguard_message_header)
        else:
            LOG.info("Drydock reports nodes: %s", node_list)

    def continue_on_fail(self):
        """Retrieve the continue_on_fail boolean value

        Fetch the continue-on-fail value from the action_info parameters and
        translate it into a boolean value.
        """
        continue_on_fail_str = str(self.action_info['parameters'].get(
            'continue-on-fail', 'false'))
        continue_on_fail = continue_on_fail_str.lower() == 'true'
        LOG.debug("continue-on-fail value is: %s, evaluates to: %s",
                  continue_on_fail_str, continue_on_fail)
        return continue_on_fail


class DrydockVerifyNodesExistOperatorPlugin(AirflowPlugin):
    """Creates DrydockVerifyNodesExistOperatorPlugin in Airflow."""

    name = 'drydock_verify_nodes_exist_operator'
    operators = [DrydockVerifyNodesExistOperator]
