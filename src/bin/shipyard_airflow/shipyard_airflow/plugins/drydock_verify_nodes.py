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


class DrydockVerifyNodesExistOperator(DrydockBaseOperator):

    """Drydock Verify nodes exist Operator

    This operator will trigger drydock to verify node for
    site update

    """

    def do_execute(self):

        LOG.info('verify_nodes_exit was invoked.')
        node_list = self.get_nodes()
        continue_on_fail = self.action_info['parameters'].get(
            'continue-on-fail', 'false')
        LOG.debug('node list is : {}'.format(node_list))
        LOG.debug('continue on fail is: {}'.format(continue_on_fail))

        if not node_list and str(continue_on_fail).lower() != 'true':
            msg = 'No nodes were found in MaaS, ' \
                  'and continue_on_fail is {} ' \
                  '-> Fail Drydock prepare and ' \
                  'deply nodes.'.format(continue_on_fail)
            LOG.error(msg)
            raise AirflowException(msg)


class DrydockVerifyNodesExistOperatorPlugin(AirflowPlugin):

    """Creates DrydockVerifyNodesExistOperatorPlugin in Airflow."""

    name = 'drydock_verify_nodes_exist_operator'
    operators = [DrydockVerifyNodesExistOperator]
