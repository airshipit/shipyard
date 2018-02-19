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

from keystoneauth1.identity import v3 as keystone_v3
from keystoneauth1 import session as keystone_session

from deckhand.client import client as deckhand_client

LOG = logging.getLogger(__name__)


class DeckhandClientFactory(object):
    """Factory for DeckhandClient to encapsulate commonly reused setup"""

    def __init__(self,
                 shipyard_conf,
                 *args, **kwargs):
        """Deckhand Client Factory

        Creates a client factory to retrieve clients
        :param shipyard_conf: Location of shipyard.conf
        """
        self.config = configparser.ConfigParser()
        self.config.read(shipyard_conf)

    def get_client(self):
        """Retrieve a deckhand client"""

        """
        Notes:
        TODO(bryan-strassner): If/when the airflow plugin modules move to using
            oslo config, consider using the example here:
            https://github.com/att-comdev/deckhand/blob/cef3b52a104e620e88a24caf70ed2bb1297c268f/deckhand/barbican/client_wrapper.py#L53
            which will load the attributes from the config more flexibly.
            Keystoneauth1 also provides for a simpler solution with:
            https://docs.openstack.org/keystoneauth/latest/api/keystoneauth1.loading.html
            if oslo config is used.
        """
        keystone_auth = {}
        # Construct Session Argument
        for attr in ('auth_url', 'password', 'project_domain_name',
                     'project_name', 'username', 'user_domain_name'):
            keystone_auth[attr] = self.config.get('keystone_authtoken', attr)

        # Set up keystone session
        auth = keystone_v3.Password(**keystone_auth)
        sess = keystone_session.Session(auth=auth)

        LOG.info("Setting up Deckhand client with parameters")
        for attr in keystone_auth:
            if attr != 'password':
                LOG.debug('%s = %s', attr, keystone_auth[attr])
        return deckhand_client.Client(session=sess, endpoint_type='internal')
