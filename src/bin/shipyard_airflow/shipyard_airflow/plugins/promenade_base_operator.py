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
import os

from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

try:
    from service_endpoint import ucp_service_endpoint
except ImportError:
    from shipyard_airflow.plugins.service_endpoint import ucp_service_endpoint

try:
    from service_token import shipyard_service_token
except ImportError:
    from shipyard_airflow.plugins.service_token import shipyard_service_token

try:
    from ucp_base_operator import UcpBaseOperator
except ImportError:
    from shipyard_airflow.plugins.ucp_base_operator import UcpBaseOperator

LOG = logging.getLogger(__name__)


class PromenadeBaseOperator(UcpBaseOperator):

    """Promenade Base Operator

    All promenade related workflow operators will use the promenade
    base operator as the parent and inherit attributes and methods
    from this class
    """

    @apply_defaults
    def __init__(self,
                 deckhand_design_ref=None,
                 deckhand_svc_type='deckhand',
                 promenade_svc_endpoint=None,
                 promenade_svc_type='kubernetesprovisioner',
                 redeploy_server=None,
                 svc_token=None,
                 *args, **kwargs):
        """Initialization of PromenadeBaseOperator object.

        :param deckhand_design_ref: A URI reference to the design documents
        :param deckhand_svc_type: Deckhand Service Type
        :param promenade_svc_endpoint: Promenade Service Endpoint
        :param promenade_svc_type: Promenade Service Type
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
        self.deckhand_design_ref = deckhand_design_ref
        self.deckhand_svc_type = deckhand_svc_type
        self.promenade_svc_endpoint = promenade_svc_endpoint
        self.promenade_svc_type = promenade_svc_type
        self.redeploy_server = redeploy_server
        self.svc_token = svc_token

    @shipyard_service_token
    def run_base(self, context):

        # Logs uuid of Shipyard action
        LOG.info("Executing Shipyard Action %s", self.action_info['id'])

        # Retrieve information of the server that we want to redeploy
        # if user executes the 'redeploy_server' dag
        if self.action_info['dag_id'] == 'redeploy_server':
            self.redeploy_server = self.action_info['parameters'].get(
                'server-name')

            if self.redeploy_server:
                LOG.info("Server to be redeployed is %s", self.redeploy_server)
            else:
                raise AirflowException('%s was unable to retrieve the '
                                       'server to be redeployed.'
                                       % self.__class__.__name__)

        # Retrieve promenade endpoint
        self.promenade_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.promenade_svc_type)

        LOG.info("Promenade endpoint is %s", self.promenade_svc_endpoint)

        # Retrieve Deckhand Endpoint Information
        deckhand_svc_endpoint = ucp_service_endpoint(
            self, svc_type=self.deckhand_svc_type)

        LOG.info("Deckhand endpoint is %s", deckhand_svc_endpoint)

        # Form Deckhand Design Reference Path
        # This URL will be used to retrieve the Site Design YAMLs
        deckhand_path = "deckhand+" + deckhand_svc_endpoint
        self.deckhand_design_ref = os.path.join(deckhand_path,
                                                "revisions",
                                                str(self.revision_id),
                                                "rendered-documents")
        if self.deckhand_design_ref:
            LOG.info("Design YAMLs will be retrieved from %s",
                     self.deckhand_design_ref)
        else:
            raise AirflowException("Unable to Retrieve Deckhand Revision "
                                   "%d!" % self.revision_id)


class PromenadeBaseOperatorPlugin(AirflowPlugin):

    """Creates PromenadeBaseOperator in Airflow."""

    name = 'promenade_base_operator_plugin'
    operators = [PromenadeBaseOperator]
