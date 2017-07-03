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
import time
import logging

from dateutil.parser import parse
from .base import BaseResource

class TriggerDagRunPollResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, dag_id, run_id):
        # Retrieve URL
        web_server_url = self.retrieve_config('base', 'web_server')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_500
            raise falcon.HTTPInternalServerError("Internal Server Error", "Missing Configuration File")
        else:
            req_url = '{}/admin/rest_api/api?api=trigger_dag&dag_id={}&run_id={}'.format(web_server_url, dag_id, run_id)
            response = requests.get(req_url).json()
       
            if response["http_response_code"] != 200:
                resp.status = falcon.HTTP_400
                resp.body = response["output"]
                return
            else:
                resp.status = falcon.HTTP_200

                logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
                logging.info("Executing '" + dag_id + "' Dag...")

                # Retrieve time of execution so that we can use it to query dag/task status
                dt = parse(response["response_time"])
                exec_date = dt.strftime('%Y-%m-%dT%H:%M:%S')

                url = '{}/admin/rest_api/api?api=dag_state&dag_id={}&execution_date={}'.format(web_server_url, dag_id, exec_date)

                # Back off for 5 seconds before querying the initial state
                time.sleep( 5 )
                dag_state = requests.get(url).json()

                # Remove newline character at the end of the response
                dag_state = dag_state["output"]["stdout"].encode('utf8').rstrip()

                while dag_state != 'success':
                    # Get current state
                    dag_state = requests.get(url).json()

                    # Remove newline character at the end of the response
                    dag_state = dag_state["output"]["stdout"].encode('utf8').rstrip()

                    # Logs output of current dag state
                    logging.info('Current Dag State: ' + dag_state)

                    if dag_state == 'failed':
                        resp.status = falcon.HTTP_500
                        logging.info('Dag Execution Failed')
                        resp.body = json.dumps({'Error': 'Dag Execution Failed'})
                        return

                    # Wait for 20 seconds before doing a new query
                    time.sleep( 20 )

                logging.info('Dag Successfully Executed')

