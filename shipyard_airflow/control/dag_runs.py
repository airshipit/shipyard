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

from .base import BaseResource

class DagRunResource(BaseResource):

    authorized_roles = ['user']

    def on_post(self, req, resp, dag_id, run_id=None, conf=None, execution_date=None):
        req_url = 'http://localhost:32080/api/experimental/dags/{}/dag_runs'.format(dag_id)

        response = requests.post(req_url,
                                 json={
                                 "run_id": run_id,
                                 "conf": conf,
                                 "execution_date": execution_date,
                             })
        if not response.ok:
            raise IOError()
        else:
            resp.status = falcon.HTTP_200

        data = response.json()

        return data['message']
