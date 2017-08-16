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


class GetAirflowVersionResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp):
        # Retrieve URL
        web_server_url = self.retrieve_config('base', 'web_server')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_500
            raise falcon.HTTPInternalServerError("Internal Server Error",
                                                 "Missing Configuration File")
        else:
            # Get Airflow Version
            req_url = '{}/admin/rest_api/api?api=version'.format(
                web_server_url)
            response = requests.get(req_url).json()

            if response["output"]:
                resp.status = falcon.HTTP_200
                resp.body = response["output"]
            else:
                self.return_error(resp, falcon.HTTP_400,
                                  'Fail to Retrieve Airflow Version')
                return
