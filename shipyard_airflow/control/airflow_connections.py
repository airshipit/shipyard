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
from urllib.parse import urlunsplit
from falcon import HTTPInvalidParam

from .base import BaseResource
from shipyard_airflow.airflow_client import AirflowClient

# We need to be able to add/delete connections so that we can create/delete
# connection endpoints that Airflow needs to connect to
class AirflowAddConnectionResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, action, conn_id, protocol, host, port):
        web_server_url = self.retrieve_config('base', 'web_server')
        if action != 'add':
            raise HTTPInvalidParam(
                'Invalid Paremeters for Adding Airflow Connection', 'action')

        # Concatenate to form the connection URL
        netloc = ''.join([host, ':', port])
        url = (protocol, netloc, '', '', '')
        conn_uri = urlunsplit(url)
        # Form the request URL towards Airflow
        req_url = ('{}/admin/rest_api/api?api=connections&add=true&conn_id'
                   '={}&conn_uri={}'.format(web_server_url, conn_id, conn_uri))

        airflow_client = AirflowClient(req_url)
        self.on_success(resp, airflow_client.get())


# Delete a particular connection endpoint
class AirflowDeleteConnectionResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, action, conn_id):
        # Retrieve URL
        web_server_url = self.retrieve_config('base', 'web_server')
        if action != 'delete':
            raise HTTPInvalidParam(
                'Invalid Paremeters for Deleting Airflow Connection', 'action')

        # Form the request URL towards Airflow
        req_url = ('{}/admin/rest_api/api?api=connections&delete=true&conn_id'
                   '={}'.format(web_server_url, conn_id))
        airflow_client = AirflowClient(req_url)
        self.on_success(resp, airflow_client.get())


# List all current connection endpoints
class AirflowListConnectionsResource(BaseResource):

    authorized_roles = ['user']

    def on_get(self, req, resp, action):
        web_server_url = self.retrieve_config('base', 'web_server')
        if action != 'list':
            raise HTTPInvalidParam(
                'Invalid Paremeters for listing Airflow Connections', 'action')

        req_url = '{}/admin/rest_api/api?api=connections&list=true'.format(
            web_server_url)

        airflow_client = AirflowClient(req_url)
        self.on_success(resp, airflow_client.get())
