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
import requests

from .client_error import ClientError


class BaseClient:
    def __init__(self, context):
        self.logger = logging.Logger('api_client')
        self.context = context

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
                'X-Auth-Token': self.context.get_token()
            }
            self.debug('Post request url: ' + url)
            self.debug('Query Params: ' + str(query_params))
            # This could use keystoneauth1 session, but that library handles
            # responses strangely (wraps all 400/500 in a keystone exception)
            return requests.post(
                url, data=data, params=query_params, headers=headers)
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
                'X-Auth-Token': self.context.get_token()
            }
            self.debug('url: ' + url)
            self.debug('Query Params: ' + str(query_params))
            return requests.get(url, params=query_params, headers=headers)
        except requests.exceptions.RequestException as e:
            self.error(str(e))
            raise ClientError(str(e))
