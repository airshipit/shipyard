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
from airflow.utils.decorators import apply_defaults

try:
    import service_endpoint
    from service_token import shipyard_service_token
    from ucp_base_operator import UcpBaseOperator
except ImportError:
    from shipyard_airflow.plugins import service_endpoint
    from shipyard_airflow.plugins.service_token import shipyard_service_token
    from shipyard_airflow.plugins.ucp_base_operator import UcpBaseOperator
from shipyard_airflow.shipyard_const import CustomHeaders

LOG = logging.getLogger(__name__)


class PromenadeBaseOperator(UcpBaseOperator):

    """Promenade Base Operator

    All promenade related workflow operators will use the promenade
    base operator as the parent and inherit attributes and methods
    from this class
    """

    @apply_defaults
    def __init__(self,
                 redeploy_server=None,
                 svc_token=None,
                 *args, **kwargs):
        """Initialization of PromenadeBaseOperator object.

        :param redeploy_server: Server to be redeployed
        :param svc_token: Keystone Token
        The Drydock operator assumes that prior steps have set xcoms for
        the action and the deployment configuration
        """

        super(PromenadeBaseOperator,
              self).__init__(
                  pod_selector_pattern=[{'pod_pattern': 'promenade-api',
                                         'container': 'promenade-api'}],
                  *args, **kwargs)
        self.redeploy_server = redeploy_server
        self.svc_token = svc_token

    @shipyard_service_token
    def run_base(self, context):

        # Logs uuid of Shipyard action
        LOG.info("Executing Shipyard Action %s", self.action_id)

        # Create additional headers dict to pass context marker
        # and end user
        addl_headers = {
            CustomHeaders.CONTEXT_MARKER.value: self.context_marker,
            CustomHeaders.END_USER.value: self.user
        }

        # Retrieve promenade endpoint
        self.promenade_svc_endpoint = self.endpoints.endpoint_by_name(
            service_endpoint.PROMENADE,
            addl_headers=addl_headers
        )

        LOG.info("Promenade endpoint is %s", self.promenade_svc_endpoint)


class PromenadeBaseOperatorPlugin(AirflowPlugin):

    """Creates PromenadeBaseOperator in Airflow."""

    name = 'promenade_base_operator_plugin'
    operators = [PromenadeBaseOperator]
