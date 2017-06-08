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
import json

from .regions import RegionsResource, RegionResource
from .base import ShipyardRequest, BaseResource
from .tasks import TaskResource

from .middleware import AuthMiddleware, ContextMiddleware, LoggingMiddleware

def start_api():
    control_api = falcon.API(request_type=ShipyardRequest,
                             middleware=[AuthMiddleware(), ContextMiddleware(), LoggingMiddleware()])

    control_api.add_route('/versions', VersionsResource())

    # v1.0 of Shipyard API
    v1_0_routes = [
        # API for managing region data
        ('/regions', RegionsResource()),
        ('/regions/{region_id}', RegionResource()),
        ('/dags/{dag_id}/tasks/{task_id}', TaskResource()),
    ]

    for path, res in v1_0_routes:
        control_api.add_route('/api/experimental' + path, res)

    return control_api

class VersionsResource(BaseResource):

    authorized_roles = ['anyone']

    def on_get(self, req, resp):
        resp.body = json.dumps({'v1.0': {
                                    'path': '/api/v1.0',
                                    'status': 'stable'
                                }})
        resp.status = falcon.HTTP_200
