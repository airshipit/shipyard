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
import urllib.parse

from .base import BaseResource

# We need to be able to add/delete connections so that we can create/delete
# connection endpoints that Airflow needs to connect to
class AirflowAddConnectionResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, action, conn_id, protocol, host, port):
        # Retrieve URL
        web_server_url = self.retrieve_config('base', 'web_server')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_500
            raise falcon.HTTPInternalServerError("Internal Server Error", "Missing Configuration File")
        else:
            if action == 'add':
                # Concatenate to form the connection URL
                netloc = ''.join([host, ':', port])
                url = (protocol, netloc, '','','')
                conn_uri = urlparse.urlunsplit(url)

                # Form the request URL towards Airflow
                req_url = '{}/admin/rest_api/api?api=connections&add=true&conn_id={}&conn_uri={}'.format(web_server_url, conn_id, conn_uri)
            else:
                self.return_error(resp, falcon.HTTP_400, 'Invalid Paremeters for Adding Airflow Connection')
                return

            response = requests.get(req_url).json()

            # Return output
            if response["output"]["stderr"]:
                resp.status = falcon.HTTP_400
                resp.body = response["output"]["stderr"]
                return
            else:
                resp.status = falcon.HTTP_200
                resp.body = response["output"]["stdout"]


# Delete a particular connection endpoint
class AirflowDeleteConnectionResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, action, conn_id):
        # Retrieve URL
        web_server_url = self.retrieve_config('base', 'web_server')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_500
            raise falcon.HTTPInternalServerError("Internal Server Error", "Missing Configuration File")
        else:
            if action == 'delete':
                # Form the request URL towards Airflow
                req_url = '{}/admin/rest_api/api?api=connections&delete=true&conn_id={}'.format(web_server_url, conn_id)
            else:
                self.return_error(resp, falcon.HTTP_400, 'Invalid Paremeters for Deleting Airflow Connection')
                return

            response = requests.get(req_url).json()

            # Return output
            if response["output"]["stderr"]:
                resp.status = falcon.HTTP_400
                resp.body = response["output"]["stderr"]
                return
            else:
                resp.status = falcon.HTTP_200
                resp.body = response["output"]["stdout"]


# List all current connection endpoints
class AirflowListConnectionsResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, action):
        # Retrieve URL
        web_server_url = self.retrieve_config('base', 'web_server')

        if 'Error' in web_server_url:
            resp.status = falcon.HTTP_500
            raise falcon.HTTPInternalServerError("Internal Server Error", "Missing Configuration File")
        else:
            if action == 'list':
                # Form the request URL towards Airflow
                req_url = '{}/admin/rest_api/api?api=connections&list=true'.format(web_server_url)
            else:
                self.return_error(resp, falcon.HTTP_400, 'Invalid Paremeters for listing Airflow Connections')
                return

            response = requests.get(req_url).json()

            # Return output
            if response["output"]["stderr"]:
                resp.status = falcon.HTTP_400
                resp.body = response["output"]["stderr"]
                return
            else:
                resp.status = falcon.HTTP_200
                resp.body = response["output"]["stdout"]

