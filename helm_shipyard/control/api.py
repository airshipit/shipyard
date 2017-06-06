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

from .tasks import TasksResource
from .base import ShipyardRequest
from .middleware import AuthMiddleware, ContextMiddleware, LoggingMiddleware

def start_api(state_manager):
    control_api = falcon.API(request_type=ShipyardRequest,
                             middleware=[AuthMiddleware(), ContextMiddleware(), LoggingMiddleware()])

    # API for managing region data
    control_api.add_route('/region/{region_id}', TasksResource)
    control_api.add_route('/region/{region_id}/server/{name}', TasksResource)
    control_api.add_route('/region/{region_id}/service/{kind}', TasksResource)

    return control_api
