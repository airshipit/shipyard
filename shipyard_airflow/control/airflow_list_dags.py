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


class ListDagsResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp):
        # Retrieve URL
        web_server_url = self.retrieve_config('base', 'web_server')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_500
            raise falcon.HTTPInternalServerError("Internal Server Error",
                                                 "Missing Configuration File")
        else:
            # List available dags
            req_url = '{}/admin/rest_api/api?api=list_dags'.format(
                web_server_url)
            response = requests.get(req_url).json()

            if response["output"]["stderr"]:
                resp.status = falcon.HTTP_400
                resp.body = response["output"]["stderr"]
                return
            else:
                resp.status = falcon.HTTP_200
                resp.body = response["output"]["stdout"]
