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
import json
import logging
import uuid

import falcon
import falcon.request as request
import falcon.routing as routing

from shipyard_airflow.common.notes.notes import MIN_VERBOSITY
from shipyard_airflow.control.json_schemas import validate_json
from shipyard_airflow.errors import InvalidFormatError

LOG = logging.getLogger(__name__)


class BaseResource(object):
    """
    The base resource for Shipyard entities/api handlers. This class
    provides some reusable functionality.
    """
    def on_options(self, req, resp, **kwargs):
        """Handle options requests"""
        method_map = routing.map_http_methods(self)
        for method in method_map:
            if method_map.get(method).__name__ != 'method_not_allowed':
                resp.append_header('Allow', method)
        resp.status = falcon.HTTP_200

    def req_json(self, req, validate_json_schema=None):
        """
        Reads and returns the input json message, optionally validates against
        a provided jsonschema
        :param req: the falcon request object
        :param validate_json_schema: the optional jsonschema to use for
                                     validation
        """
        has_input = False
        if (req.content_length is not None and 'application/json' in
                req.content_type):
            raw_body = req.stream.read(req.content_length or 0)
            if raw_body is not None:
                has_input = True
                LOG.info('Input message body: %s', raw_body)
            else:
                LOG.info('No message body specified')
        if has_input:
            # read the json and validate if necessary
            try:
                raw_body = raw_body.decode('utf-8')
                json_body = json.loads(raw_body)
                if validate_json_schema:
                    # rasises an exception if it doesn't validate
                    validate_json(json_body, validate_json_schema)
                return json_body
            except json.JSONDecodeError as jex:
                LOG.error("Invalid JSON in request: %s", raw_body)
                raise InvalidFormatError(
                    title='JSON could not be decoded',
                    description='%s: Invalid JSON in body: %s' %
                    (req.path, jex)
                )
        else:
            # No body passed as input. Fail validation if it was asked for
            if validate_json_schema is not None:
                raise InvalidFormatError(
                    title='Json body is required',
                    description='%s: Bad input, no body provided' %
                    (req.path)
                )
            else:
                return None

    def to_json(self, body_dict):
        """Thin wrapper around json.dumps, providing the default=str config"""
        return json.dumps(body_dict, default=str)


class ShipyardRequestContext(object):
    """
    Context object for shipyard resource requests
    """

    def __init__(self):
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
        self.verbosity = MIN_VERBOSITY

    def set_user(self, user):
        self.user = user

    def set_project(self, project):
        self.project = project

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        self.roles.extend(roles)

    def remove_role(self, role):
        self.roles = [x for x in self.roles if x != role]

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


class ShipyardRequest(request.Request):
    context_type = ShipyardRequestContext
