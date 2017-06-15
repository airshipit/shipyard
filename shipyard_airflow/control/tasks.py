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
import requests

from .base import BaseResource

class TaskResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, dag_id, task_id):
        # Retrieve URL
        web_server_url = self.retrieve_config('BASE', 'WEB_SERVER')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_400
            resp.body = json.dumps({'Error': 'Missing Configuration File'})
            return
        else:
            req_url = '{}/api/experimental/dags/{}/tasks/{}'.format(web_server_url, dag_id, task_id)
            task_details = requests.get(req_url).json()

            if 'error' in task_details:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(task_details)
                return
            else:
                resp.status = falcon.HTTP_200
                resp.body = json.dumps(task_details)

