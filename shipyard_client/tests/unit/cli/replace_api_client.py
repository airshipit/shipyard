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

# For testing purposes only


class TemporaryContext(object):
    def __init__(self):
        self.debug = True
        self.keystone_Auth = {}
        self.token = 'abcdefgh'
        self.service_type = 'http://shipyard'
        self.shipyard_endpoint = 'http://shipyard/api/v1.0'
        self.context_marker = '123456'


def replace_post_rep(self, url, query_params={}, data={}, content_type=''):
    """
    replaces call to shipyard client
    :returns: dict with url and parameters
    """
    return {'url': url, 'params': query_params, 'data': data}


def replace_get_resp(self, url, query_params={}, json=False):
    """
    replaces call to shipyard client
    :returns: dict with url and parameters
    """
    return {'url': url, 'params': query_params}


def replace_base_constructor(self, context):
    pass


def replace_output_formatting(format, response):
    return response
