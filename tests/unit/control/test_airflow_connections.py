# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import falcon
from falcon import testing
import mock

from shipyard_airflow.control import api
from shipyard_airflow.control.airflow_connections import (
    AirflowAddConnectionResource,
    AirflowDeleteConnectionResource,
    AirflowListConnectionsResource,
)


class BaseTesting(testing.TestCase):
    def setUp(self):
        super().setUp()
        self.app = api.start_api()
        self.conn_id = 1
        self.protocol = 'http'
        self.host = '10.0.0.1'
        self.port = '3000'

    @property
    def _headers(self):
        return {
            'X-Auth-Token': '10'
        }


class AirflowAddConnectionResourceTestCase(BaseTesting):
    def setUp(self):
        super().setUp()
        self.action = 'add'

    @property
    def _url(self):
        return ('/api/v1.0/connections/{}/conn_id/{}/'
                'protocol/{}/host/{}/port/{}'.format(
                    self.action, self.conn_id,
                    self.protocol, self.host, self.port))

    def test_on_get_missing_config_file(self):
        doc = {
            'description': 'Missing Configuration File',
            'message': 'Internal Server Error'
        }
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_500

    @mock.patch.object(AirflowAddConnectionResource, 'retrieve_config')
    def test_on_get_invalid_action(self, mock_config):
        self.action = 'invalid_action'
        doc = {
            'title': 'Invalid parameter',
            'description': ('The "action" parameter is invalid.'
                            ' Invalid Paremeters for Adding Airflow'
                            ' Connection')
        }
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_400
        mock_config.assert_called_once_with('base', 'web_server')

    @mock.patch('shipyard_airflow.airflow_client.requests')
    @mock.patch.object(AirflowAddConnectionResource, 'retrieve_config')
    def test_on_get_airflow_error(self, mock_config, mock_requests):
        doc = {
            'message': 'Error response from Airflow',
            'description': "can't add connections in airflow"
        }
        mock_response = {
            'output': {
                'stderr': "can't add connections in airflow"
            }
        }
        mock_requests.get.return_value.json.return_value = mock_response
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_400
        mock_config.assert_called_once_with('base', 'web_server')

    @mock.patch('shipyard_airflow.airflow_client.requests')
    @mock.patch.object(AirflowAddConnectionResource, 'retrieve_config')
    def test_on_get_airflow_success(self, mock_config, mock_requests):
        doc = {
            'type': 'success',
            'message': 'Airflow Success',
        }
        mock_response = {
            'output': {
                'stderr': None,
                'stdout': 'Airflow Success'
            }
        }
        mock_requests.get.return_value.json.return_value = mock_response
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_200
        mock_config.assert_called_once_with('base', 'web_server')


class AirflowDeleteConnectionResource(BaseTesting):
    def setUp(self):
        self.action = 'delete'
        super().setUp()

    @property
    def _url(self):
        return '/api/v1.0/connections/{}/conn_id/{}'.format(
            self.action, self.conn_id)

    def test_on_get_missing_config_file(self):
        doc = {
            'description': 'Missing Configuration File',
            'message': 'Internal Server Error'
        }
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_500

    @mock.patch.object(AirflowDeleteConnectionResource, 'retrieve_config')
    def test_on_get_invalid_action(self, mock_config):
        self.action = 'invalid_action'
        doc = {
            'title': 'Invalid parameter',
            'description': ('The "action" parameter is invalid.'
                            ' Invalid Paremeters for Deleting Airflow'
                            ' Connection')
        }
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_400
        mock_config.assert_called_once_with('base', 'web_server')

    @mock.patch('shipyard_airflow.airflow_client.requests')
    @mock.patch.object(AirflowDeleteConnectionResource, 'retrieve_config')
    def test_on_get_airflow_error(self, mock_config, mock_requests):
        doc = {
            'message': 'Error response from Airflow',
            'description': "can't delete connections in airflow"
        }
        mock_response = {
            'output': {
                'stderr': "can't delete connections in airflow"
            }
        }
        mock_requests.get.return_value.json.return_value = mock_response
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)

        assert result.json == doc
        assert result.status == falcon.HTTP_400
        mock_config.assert_called_once_with('base', 'web_server')

    @mock.patch('shipyard_airflow.airflow_client.requests')
    @mock.patch.object(AirflowDeleteConnectionResource, 'retrieve_config')
    def test_on_get_airflow_success(self, mock_config, mock_requests):
        doc = {
            'type': 'success',
            'message': 'Airflow Success',
        }
        mock_response = {
            'output': {
                'stderr': None,
                'stdout': 'Airflow Success'
            }
        }
        mock_requests.get.return_value.json.return_value = mock_response
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_200
        mock_config.assert_called_once_with('base', 'web_server')


class AirflowListConnectionsResource(BaseTesting):
    def setUp(self):
        self.action = 'list'
        super().setUp()

    @property
    def _url(self):
        return '/api/v1.0/connections/{}'.format(self.action)

    def test_on_get_missing_config_file(self):
        doc = {
            'description': 'Missing Configuration File',
            'message': 'Internal Server Error'
        }
        result = self.simulate_get(self._url, headers=self._headers)
        assert result.json == doc
        assert result.status == falcon.HTTP_500

    @mock.patch.object(AirflowListConnectionsResource, 'retrieve_config')
    def test_on_get_invalid_action(self, mock_config):
        self.action = 'invalid_action'
        doc = {
            'title': 'Invalid parameter',
            'description': ('The "action" parameter is invalid.'
                            ' Invalid Paremeters for listing Airflow'
                            ' Connections')
        }
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)

        assert result.json == doc
        assert result.status == falcon.HTTP_400
        mock_config.assert_called_once_with('base', 'web_server')

    @mock.patch('shipyard_airflow.airflow_client.requests')
    @mock.patch.object(AirflowListConnectionsResource, 'retrieve_config')
    def test_on_get_airflow_error(self, mock_config, mock_requests):
        doc = {
            'message': 'Error response from Airflow',
            'description': "can't list connections in airlfow"
        }
        mock_response = {
            'output': {
                'stderr': "can't list connections in airlfow"
            }
        }
        mock_requests.get.return_value.json.return_value = mock_response
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)

        assert result.json == doc
        assert result.status == falcon.HTTP_400
        mock_config.assert_called_once_with('base', 'web_server')

    @mock.patch('shipyard_airflow.airflow_client.requests')
    @mock.patch.object(AirflowListConnectionsResource, 'retrieve_config')
    def test_on_get_airflow_success(self, mock_config, mock_requests):
        doc = {
            'type': 'success',
            'message': 'Airflow Success',
        }
        mock_response = {
            'output': {
                'stderr': None,
                'stdout': 'Airflow Success'
            }
        }
        mock_requests.get.return_value.json.return_value = mock_response
        mock_config.return_value = 'some_url'
        result = self.simulate_get(self._url, headers=self._headers)

        assert result.json == doc
        assert result.status == falcon.HTTP_200
        mock_config.assert_called_once_with('base', 'web_server')
