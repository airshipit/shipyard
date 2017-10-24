# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from keystoneauth1 import session
from keystoneauth1.identity import v3
from keystoneauth1.exceptions.auth import AuthorizationFailure
from keystoneauth1.exceptions.catalog import EndpointNotFound
from .client_error import ClientError

LOG = logging.getLogger(__name__)


class ShipyardClientContext:
    def __init__(self, keystone_auth, context_marker, debug=False):
        """
        shipyard context object
        :param bool debug: true, or false
        :param str context_marker:
        :param dict keystone_auth: auth_url, password, project_domain_name,
               project_name, username, user_domain_name
        """
        self.debug = debug
        self.keystone_auth = keystone_auth
        # the service type will for now just be shipyard will change later
        self.service_type = 'shipyard'
        self.shipyard_endpoint = self.get_endpoint()
        self.set_debug()
        self.context_marker = context_marker

    def set_debug(self):
        if self.debug:
            LOG.setLevel(logging.DEBUG)

    def get_token(self):
        """
        Returns the simple token string for a token acquired from keystone
        """
        return self._get_ks_session().get_auth_headers().get('X-Auth-Token')

    def _get_ks_session(self):
        LOG.debug('Accessing keystone for keystone session')
        try:
            auth = v3.Password(**self.keystone_auth)
            return session.Session(auth=auth)
        except AuthorizationFailure as e:
            LOG.error('Could not authorize against keystone: %s', str(e))
            raise ClientError(str(e))

    def get_endpoint(self):
        """
        Wraps calls to keystone for lookup with overrides from configuration
        """
        LOG.debug('Accessing keystone for %s endpoint', self.service_type)
        try:
            return self._get_ks_session().get_endpoint(
                interface='public', service_type=self.service_type)
        except EndpointNotFound as e:
            LOG.error('Could not find a public interface for %s',
                      self.service_type)
            raise ClientError(str(e))
