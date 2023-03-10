# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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

import falcon
from falcon import testing

AUTH_HEADERS = {
    'X-SERVICE-IDENTITY-STATUS': 'Confirmed',
    'X-IDENTITY-STATUS': 'Confirmed',
    'X-SERVICE-USER-NAME': 'testauth',
    'X-USER-NAME': 'testauth',
    'X-SERVICE-USER-ID': 'testauth',
    'X-USER-ID': 'testauth',
    'X-SERVICE-USER-DOMAIN-ID': 'default',
    'X-USER-DOMAIN-ID': 'default',
    'X-SERVICE-PROJECT-ID': 'default',
    'X-PROJECT-ID': 'default',
    'X-SERVICE-PROJECT-DOMAIN-ID': 'default',
    'X-PROJECT-DOMAIN-NAME': 'default',
    'X-SERVICE-ROLES': 'Admin',
    'X-ROLES': 'Admin',
    'X-IS-ADMIN-PROJECT': 'True'
}


def create_req(ctx, body):
    '''creates a falcon request'''
    env = testing.create_environ(
        path='/',
        query_string='',
        http_version='1.1',
        scheme='http',
        host='falconframework.org',
        port=None,
        headers={'Content-Type': 'application/json'},
        root_path='',
        body=body,
        method='POST',
        wsgierrors=None,
        file_wrapper=None)
    req = falcon.Request(env)
    req.context = ctx
    return req


def create_resp():
    '''creates a falcon response'''
    resp = falcon.Response()
    return resp


def str_responder(*args, **kwargs):
    """Responds with an empty string"""
    return ''
