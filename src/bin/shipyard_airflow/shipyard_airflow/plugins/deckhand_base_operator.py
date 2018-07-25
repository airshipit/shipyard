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
import configparser
import logging

from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

from deckhand.client import client as deckhand_client

try:
    import service_endpoint
    from service_token import shipyard_service_token
    from ucp_base_operator import UcpBaseOperator
except ImportError:
    from shipyard_airflow.plugins import service_endpoint
    from shipyard_airflow.plugins.service_token import shipyard_service_token
    from shipyard_airflow.plugins.ucp_base_operator import UcpBaseOperator

LOG = logging.getLogger(__name__)


class DeckhandBaseOperator(UcpBaseOperator):

    """Deckhand Base Operator

    All deckhand related workflow operators will use the deckhand
    base operator as the parent and inherit attributes and methods
    from this class

    """

    @apply_defaults
    def __init__(self,
                 committed_ver=None,
                 deckhandclient=None,
                 deckhand_client_read_timeout=None,
                 revision_id=None,
                 svc_session=None,
                 svc_token=None,
                 validation_read_timeout=None,
                 *args, **kwargs):
        """Initialization of DeckhandBaseOperator object.

        :param committed_ver: Last committed version
        :param deckhandclient: An instance of deckhand client
        :param deckhand_client_read_timeout: Deckhand client connect timeout
        :param revision_id: Target revision for workflow
        :param svc_session: Keystone Session
        :param svc_token: Keystone Token
        :param validation_read_timeout: Deckhand validation timeout

        """

        super(DeckhandBaseOperator,
              self).__init__(
                  pod_selector_pattern=[{'pod_pattern': 'deckhand-api',
                                         'container': 'deckhand-api'}],
                  *args, **kwargs)
        self.committed_ver = committed_ver
        self.deckhandclient = deckhandclient
        self.deckhand_client_read_timeout = deckhand_client_read_timeout
        self.revision_id = revision_id
        self.svc_session = svc_session
        self.svc_token = svc_token
        self.validation_read_timeout = validation_read_timeout

    @shipyard_service_token
    def run_base(self, context):

        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        # Initialize variables
        self.deckhand_client_read_timeout = int(config.get(
            'requests_config', 'deckhand_client_read_timeout'))

        self.validation_read_timeout = int(config.get(
            'requests_config', 'validation_read_timeout'))

        # Logs uuid of Shipyard action
        LOG.info("Executing Shipyard Action %s",
                 self.action_info['id'])

        # Retrieve Endpoint Information
        self.deckhand_svc_endpoint = self.endpoints.endpoint_by_name(
            service_endpoint.DECKHAND
        )

        LOG.info("Deckhand endpoint is %s",
                 self.deckhand_svc_endpoint)

        # Set up DeckHand Client
        LOG.info("Setting up DeckHand Client...")

        # NOTE: The communication between the Airflow workers
        # and Deckhand happens via the 'internal' endpoint.
        self.deckhandclient = deckhand_client.Client(
            session=self.svc_session, endpoint_type='internal')

        if not self.deckhandclient:
            raise AirflowException('Failed to set up deckhand client!')


class DeckhandBaseOperatorPlugin(AirflowPlugin):

    """Creates DeckhandBaseOperator in Airflow."""

    name = 'deckhand_base_operator_plugin'
