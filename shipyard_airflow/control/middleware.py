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
import logging

from oslo_utils import uuidutils

from shipyard_airflow import policy


class AuthMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger('shipyard')

    # Authentication
    def process_request(self, req, resp):
        ctx = req.context
        ctx.set_policy_engine(policy.policy_engine)

        for k, v in req.headers.items():
            self.logger.debug("Request with header %s: %s" % (k, v))

        auth_status = req.get_header(
            'X-SERVICE-IDENTITY-STATUS')  # will be set to Confirmed or Invalid
        service = True

        if auth_status is None:
            auth_status = req.get_header('X-IDENTITY-STATUS')
            service = False

        if auth_status == 'Confirmed':
            # Process account and roles
            ctx.authenticated = True
            # User Identity, unique within owning domain
            ctx.user = req.get_header(
                'X-SERVICE-USER-NAME') if service else req.get_header(
                    'X-USER-NAME')
            # Identity-service managed unique identifier
            ctx.user_id = req.get_header(
                'X-SERVICE-USER-ID') if service else req.get_header(
                    'X-USER-ID')
            # Identity service managed unique identifier of owning domain of
            #  user name
            ctx.user_domain_id = req.get_header(
                'X-SERVICE-USER-DOMAIN-ID') if service else req.get_header(
                    'X-USER-DOMAIN-ID')
            # Identity service managed unique identifier
            ctx.project_id = req.get_header(
                'X-SERVICE-PROJECT-ID') if service else req.get_header(
                    'X-PROJECT-ID')
            # Name of owning domain of project
            ctx.project_domain_id = req.get_header(
                'X-SERVICE-PROJECT-DOMAIN-ID') if service else req.get_header(
                    'X-PROJECT-DOMAIN-NAME')
            if service:
                # comma delimieted list of case-sensitive role names
                ctx.add_roles(req.get_header('X-SERVICE-ROLES').split(','))
            else:
                ctx.add_roles(req.get_header('X-ROLES').split(','))

            if req.get_header('X-IS-ADMIN-PROJECT') == 'True':
                ctx.is_admin_project = True
            else:
                ctx.is_admin_project = False

            self.logger.debug(
                'Request from authenticated user %s with roles %s',
                ctx.user, ','.join(ctx.roles)
            )
        else:
            ctx.authenticated = False


class ContextMiddleware(object):
    """
    Handle looking at the X-Context_Marker to see if it has value and that
    value is a UUID (or close enough). If not, generate one.
    """
    def process_request(self, req, resp):
        ctx = req.context
        ext_marker = req.get_header('X-Context-Marker')
        if ext_marker is not None and uuidutils.is_uuid_like(ext_marker):
            # external passed in an ok context marker
            ctx.set_external_marker(ext_marker)
        else:
            # use the request id
            ctx.set_external_marker(ctx.request_id)


class LoggingMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger('shipyard.control')

    def process_response(self, req, resp, resource, req_succeeded):
        ctx = req.context

        extra = {
            'user': ctx.user,
            'req_id': ctx.request_id,
            'external_ctx': ctx.external_marker,
        }

        resp.append_header('X-Shipyard-Req', ctx.request_id)
        self.logger.info('%s %s - %s',
                         req.method,
                         req.uri,
                         resp.status,
                         extra=extra)
        self.logger.debug('Response body:\n%s',
                          resp.body,
                          extra=extra)
