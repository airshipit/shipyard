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
import uuid
import json
import configparser
import os
import logging

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from shipyard_airflow.errors import (
    AppError,
    ERR_UNKNOWN,
)


class BaseResource(object):

    def on_options(self, req, resp):
        self_attrs = dir(self)
        methods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH']
        allowed_methods = []

        for m in methods:
            if 'on_' + m.lower() in self_attrs:
                allowed_methods.append(m)

        resp.headers['Allow'] = ','.join(allowed_methods)
        resp.status = falcon.HTTP_200

    def to_json(self, body_dict):
        return json.dumps(body_dict)

    def on_success(self, res, message=None):
        res.status = falcon.HTTP_200
        response_dict = OrderedDict()
        response_dict['type'] = 'success'
        response_dict['message'] = message
        res.body = self.to_json(response_dict)

    # Error Handling
    def return_error(self, resp, status_code, message="", retry=False):
        """
        Write a error message body and throw a Falcon exception to trigger
        an HTTP status

        :param resp: Falcon response object to update
        :param status_code: Falcon status_code constant
        :param message: Optional error message to include in the body
        :param retry: Optional flag whether client should retry the operation.
        Can ignore if we rely solely on 4XX vs 5xx status codes
        """
        resp.body = self.to_json(
            {'type': 'error', 'message': message, 'retry': retry})
        resp.content_type = 'application/json'
        resp.status = status_code

    # Get Config Data
    def retrieve_config(self, section="", data=""):

        # Shipyard config will be located at /etc/shipyard/shipyard.conf
        path = '/etc/shipyard/shipyard.conf'

        # Check that shipyard.conf exists
        if os.path.isfile(path):
            config = configparser.ConfigParser()
            config.read(path)

            # Retrieve data from shipyard.conf
            query_data = config.get(section, data)

            return query_data
        else:
            raise AppError(ERR_UNKNOWN, "Missing Configuration File")

    def error(self, ctx, msg):
        self.log_error(ctx, logging.ERROR, msg)

    def info(self, ctx, msg):
        self.log_error(ctx, logging.INFO, msg)

    def log_error(self, ctx, level, msg):
        extra = {
            'user': 'N/A',
            'req_id': 'N/A',
            'external_ctx': 'N/A'
        }

        if ctx is not None:
            extra = {
                'user': ctx.user,
                'req_id': ctx.request_id,
                'external_ctx': ctx.external_marker,
            }

class ShipyardRequestContext(object):

    def __init__(self):
        self.log_level = 'error'
        self.user = None
        self.roles = ['anyone']
        self.request_id = str(uuid.uuid4())
        self.external_marker = None
        self.project_id = None
        self.user_id = None  # User ID (UUID)
        self.policy_engine = None
        self.user_domain_id = None  # Domain owning user
        self.project_domain_id = None  # Domain owning project
        self.is_admin_project = False
        self.authenticated = False
        self.request_id = str(uuid.uuid4())

    def set_log_level(self, level):
        if level in ['error', 'info', 'debug']:
            self.log_level = level

    def set_user(self, user):
        self.user = user

    def set_project(self, project):
        self.project = project

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        self.roles.extend(roles)

    def remove_role(self, role):
        self.roles = [x for x in self.roles
                      if x != role]

    def set_external_marker(self, marker):
        self.external_marker = marker

    def set_policy_engine(self, engine):
        self.policy_engine = engine

    def to_policy_view(self):
        policy_dict = {}

        policy_dict['user_id'] = self.user_id
        policy_dict['user_domain_id'] = self.user_domain_id
        policy_dict['project_id'] = self.project_id
        policy_dict['project_domain_id'] = self.project_domain_id
        policy_dict['roles'] = self.roles
        policy_dict['is_admin_project'] = self.is_admin_project

        return policy_dict

class ShipyardRequest(falcon.request.Request):
    context_type = ShipyardRequestContext
