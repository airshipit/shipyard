# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
import abc
import os
import logging

from keystoneauth1.exceptions.auth import AuthorizationFailure
from keystoneauth1.exceptions.catalog import EndpointNotFound
from keystoneauth1.identity import v3
from keystoneauth1 import session
import requests

from shipyard_client.api_client.client_error import ClientError
from shipyard_client.api_client.client_error import UnauthenticatedClientError
from shipyard_client.api_client.client_error import UnauthorizedClientError
from shipyard_client.api_client.client_error import ShipyardBufferError
from shipyard_client.api_client.client_error import InvalidCollectionError


class BaseClient(metaclass=abc.ABCMeta):
    """Abstract base client class

    Requrires the definition of service_type and interface by child classes
    """
    @property
    @abc.abstractmethod
    def service_type(self):
        """Specify the name/type used to lookup the service"""
        pass

    @property
    @abc.abstractmethod
    def interface(self):
        """The interface to choose from during service lookup

        Specify the interface to look up the service: public, internal admin
        """
        pass

    def __init__(self, context):
        self.logger = logging.Logger('api_client')
        self.context = context
        self.endpoint = None

    def log_message(self, level, msg):
        """ Logs a message with context, and extra populated. """
        self.logger.log(level, msg)

    def debug(self, msg):
        """ Debug logger for resources, incorporating context. """
        self.log_message(logging.DEBUG, msg)

    def info(self, ctx, msg):
        """ Info logger for resources, incorporating context. """
        self.log_message(logging.INFO, msg)

    def warn(self, msg):
        """ Warn logger for resources, incorporating context. """
        self.log_message(logging.WARN, msg)

    def error(self, msg):
        """ Error logger for resources, incorporating context. """
        self.log_message(logging.ERROR, msg)

    def post_resp(self,
                  url,
                  query_params=None,
                  data=None,
                  content_type='application/x-yaml'):
        """ Thin wrapper of requests post """
        if not query_params:
            query_params = {}
        if not data:
            data = {}
        try:
            headers = {
                'X-Context-Marker': self.context.context_marker,
                'content-type': content_type,
                'X-Auth-Token': self.get_token()
            }
            query_params['verbosity'] = self.context.verbosity
            self.debug('Post request url: ' + url)
            self.debug('Query Params: ' + str(query_params))
            # This could use keystoneauth1 session, but that library handles
            # responses strangely (wraps all 400/500 in a keystone exception)
            response = requests.post(
                url, data=data, params=query_params, headers=headers)
            # handle some cases where the response code is sufficient to know
            # what needs to be done
            if response.status_code == 401:
                raise UnauthenticatedClientError()
            if response.status_code == 403:
                raise UnauthorizedClientError()
            if response.status_code == 400:
                raise InvalidCollectionError(response.text)
            if response.status_code == 409:
                raise ShipyardBufferError(response.text)
            return response
        except requests.exceptions.RequestException as e:
            self.error(str(e))
            raise ClientError(str(e))

    def get_resp(self, url, query_params=None):
        """ Thin wrapper of requests get """
        if not query_params:
            query_params = {}
        try:
            headers = {
                'X-Context-Marker': self.context.context_marker,
                'X-Auth-Token': self.get_token()
            }
            query_params['verbosity'] = self.context.verbosity
            self.debug('url: ' + url)
            self.debug('Query Params: ' + str(query_params))
            response = requests.get(url, params=query_params, headers=headers)
            # handle some cases where the response code is sufficient to know
            # what needs to be done
            if response.status_code == 401:
                raise UnauthenticatedClientError()
            if response.status_code == 403:
                raise UnauthorizedClientError()
            return response
        except requests.exceptions.RequestException as e:
            self.error(str(e))
            raise ClientError(str(e))

    def get_token(self):
        """Returns the simple token string for a token

        Attempt to read token from environment variable, if present use it.
        If not, return the token obtained from Keystone.
        """
        token = os.environ.get('OS_AUTH_TOKEN')
        if token:
            return token
        else:
            return self._get_ks_session().get_auth_headers().get('X-Auth-Token')

    def _get_ks_session(self):
        self.logger.debug('Accessing keystone for keystone session')
        try:
            auth = v3.Password(**self.context.keystone_auth)
            return session.Session(auth=auth)
        except AuthorizationFailure as e:
            self.logger.error('Could not authorize against keystone: %s',
                              str(e))
            raise ClientError(str(e))

    def get_endpoint(self):
        """Lookup the endpoint for the client. Cache it.

        Uses a keystone session to find an endpoint for the specified
        service_type at the specified interface (public, internal, admin)
        """
        if self.endpoint is None:
            self.logger.debug('Accessing keystone for %s endpoint',
                              self.service_type)
            try:
                self.endpoint = self._get_ks_session().get_endpoint(
                    interface=self.interface, service_type=self.service_type)
            except EndpointNotFound as e:
                self.logger.error('Could not find %s interface for %s',
                                  self.interface, self.service_type)
                raise ClientError(str(e))
        return self.endpoint
