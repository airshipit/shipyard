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
import falcon, falcon.request as request
import uuid
import json
import configparser
import os

class BaseResource(object):

    authorized_roles = []

    def on_options(self, req, resp):
        self_attrs = dir(self)
        methods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH']
        allowed_methods = []

        for m in methods:
            if 'on_' + m.lower() in self_attrs:
                allowed_methods.append(m)

        resp.headers['Allow'] = ','.join(allowed_methods)
        resp.status = falcon.HTTP_200

    # By default, no one is authorized to use a resource
    def authorize_roles(self, role_list):
        authorized = set(self.authorized_roles)
        applied = set(role_list)

        if authorized.isdisjoint(applied):
            return False
        else:
            return True

    # Error Handling
    def return_error(self, resp, status_code, message="", retry=False):
        """
        Write a error message body and throw a Falcon exception to trigger an HTTP status

        :param resp: Falcon response object to update
        :param status_code: Falcon status_code constant
        :param message: Optional error message to include in the body
        :param retry: Optional flag whether client should retry the operation. Can ignore if we rely solely on 4XX vs 5xx status codes
        """
        resp.body = json.dumps({'type': 'error', 'message': message, 'retry': retry})
        resp.content_type = 'application/json'
        resp.status = status_code

    # Get Config Data
    def retrieve_config(self, section="", data=""):

        # The current assumption is that shipyard.conf will be placed in a fixed path
        # within the shipyard container - Path TBD
        path = '/home/ubuntu/att-comdev/shipyard/shipyard_airflow/control/shipyard.conf'
        
        # Check that shipyard.conf exists
        if os.path.isfile(path):
            config = configparser.ConfigParser()
            config.read(path)

            # Retrieve data from shipyard.conf
            query_data = config.get(section, data)

            return query_data
        else:
            return 'Error - Missing Configuration File'


class ShipyardRequestContext(object):

    def __init__(self):
        self.log_level = 'error'
        self.user = None
        self.roles = ['anyone']
        self.request_id = str(uuid.uuid4())
        self.external_marker = None

    def set_log_level(self, level):
        if level in ['error', 'info', 'debug']:
            self.log_level = level

    def set_user(self, user):
        self.user = user

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        self.roles.extend(roles)

    def remove_role(self, role):
        self.roles = [x for x in self.roles
                      if x != role]

    def set_external_marker(self, marker):
        self.external_marker = str(marker)[:32]

class ShipyardRequest(request.Request):
    context_type = ShipyardRequestContext

