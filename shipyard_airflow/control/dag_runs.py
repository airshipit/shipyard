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
import requests
import json

from .base import BaseResource

class DagRunResource(BaseResource):

    authorized_roles = ['user']

    def on_post(self, req, resp, dag_id, run_id=None, conf=None, execution_date=None):
        # Retrieve URL
        web_server_url = self.retrieve_config('BASE', 'WEB_SERVER')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_400
            resp.body = json.dumps({'Error': 'Missing Configuration File'})
            return
        else:
            req_url = '{}/api/experimental/dags/{}/dag_runs'.format(web_server_url, dag_id)
 
            response = requests.post(req_url,
                                     json={
                                     "run_id": run_id,
                                     "conf": conf,
                                     "execution_date": execution_date,
                                 })

            if response.ok:
                resp.status = falcon.HTTP_200
            else:
                self.return_error(resp, falcon.HTTP_400, 'Fail to Execute Dag')
                return

