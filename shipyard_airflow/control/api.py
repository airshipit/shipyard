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
from .dag_runs import DagRunResource
from .airflow_get_task_status import GetTaskStatusResource
from .airflow_list_tasks import ListTasksResource
from .airflow_list_dags import ListDagsResource
from .airflow_dag_state import GetDagStateResource
from .airflow_trigger_dag import TriggerDagRunResource
from .airflow_trigger_dag_poll import TriggerDagRunPollResource
from .airflow_connections import AirflowAddConnectionResource
from .airflow_connections import AirflowDeleteConnectionResource
from .airflow_connections import AirflowListConnectionsResource
from .airflow_get_version import GetAirflowVersionResource
from .middleware import AuthMiddleware, ContextMiddleware, LoggingMiddleware
from shipyard_airflow.errors import AppError


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
        ('/regions', RegionsResource()),
        ('/regions/{region_id}', RegionResource()),
        ('/dags/{dag_id}/tasks/{task_id}', TaskResource()),
        ('/dags/{dag_id}/dag_runs', DagRunResource()),
        ('/list_dags', ListDagsResource()),
        ('/task_state/dags/{dag_id}/tasks/{task_id}/execution_date/'
         '{execution_date}', GetTaskStatusResource()),
        ('/dag_state/dags/{dag_id}/execution_date/{execution_date}',
            GetDagStateResource()),
        ('/list_tasks/dags/{dag_id}', ListTasksResource()),
        ('/trigger_dag/dags/{dag_id}/conf/{conf}',
            TriggerDagRunResource()),
        ('/trigger_dag/dags/{dag_id}/run_id/{run_id}/poll',
            TriggerDagRunPollResource()),
        ('/connections/{action}/conn_id/{conn_id}/protocol/{protocol}'
         '/host/{host}/port/{port}', AirflowAddConnectionResource()),
        ('/connections/{action}/conn_id/{conn_id}',
            AirflowDeleteConnectionResource()),
        ('/connections/{action}', AirflowListConnectionsResource()),
        ('/airflow/version', GetAirflowVersionResource()),
    ]

    for path, res in v1_0_routes:
        control_api.add_route('/api/v1.0' + path, res)

    control_api.add_error_handler(AppError, AppError.handle)
    return control_api

class VersionsResource(BaseResource):

    authorized_roles = ['anyone']

    def on_get(self, req, resp):
        resp.body = json.dumps({
            'v1.0': {
                'path': '/api/v1.0',
                'status': 'stable'
            }})
        resp.status = falcon.HTTP_200
