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

import falcon

from shipyard_airflow.control.actions_api import ActionsResource
from shipyard_airflow.control.actions_control_api import ActionsControlResource
from shipyard_airflow.control.actions_id_api import ActionsIdResource
from shipyard_airflow.control.actions_steps_id_api import ActionsStepsResource
from shipyard_airflow.control.actions_validations_id_api import \
    ActionsValidationsResource
from shipyard_airflow.control.base import BaseResource, ShipyardRequest
from shipyard_airflow.control.health import HealthResource
from shipyard_airflow.control.middleware import (AuthMiddleware,
                                                 ContextMiddleware,
                                                 LoggingMiddleware)
from shipyard_airflow.errors import (AppError, default_error_serializer,
                                     default_exception_handler)

LOG = logging.getLogger(__name__)


def start_api():
    middlewares = [
        AuthMiddleware(),
        ContextMiddleware(),
        LoggingMiddleware(),
    ]
    control_api = falcon.API(
        request_type=ShipyardRequest, middleware=middlewares)

    control_api.add_route('/versions', VersionsResource())

    # v1.0 of Shipyard API
    v1_0_routes = [
        # API for managing region data
        ('/health', HealthResource()),
        ('/actions', ActionsResource()),
        ('/actions/{action_id}', ActionsIdResource()),
        ('/actions/{action_id}/control/{control_verb}',
         ActionsControlResource()),
        ('/actions/{action_id}/steps/{step_id}',
         ActionsStepsResource()),
        ('/actions/{action_id}/validations/{validation_id}',
         ActionsValidationsResource()),
    ]

    # Set up the 1.0 routes
    route_v1_0_prefix = '/api/v1.0'
    for path, res in v1_0_routes:
        route = '{}{}'.format(route_v1_0_prefix, path)
        LOG.info(
            'Adding route: %s Handled by %s',
            route,
            res.__class__.__name__
        )
        control_api.add_route(route, res)

    # Error handlers (FILO handling)
    control_api.add_error_handler(Exception, default_exception_handler)
    control_api.add_error_handler(AppError, AppError.handle)

    # built-in error serializer
    control_api.set_error_serializer(default_error_serializer)

    return control_api

class VersionsResource(BaseResource):
    """
    Lists the versions supported by this API
    """
    def on_get(self, req, resp):
        resp.body = self.to_json({
            'v1.0': {
                'path': '/api/v1.0',
                'status': 'stable'
            }})
        resp.status = falcon.HTTP_200
