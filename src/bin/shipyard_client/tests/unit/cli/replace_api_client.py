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


def replace_get_endpoint():
    """Replaces the get endpoint call to isolate tests"""
    return 'http://shipyard-test'


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
