# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
from datetime import datetime
from unittest import mock
from unittest.mock import patch

import falcon
import pytest
import requests

from shipyard_airflow.control.action.actions_steps_id_logs_api import \
    ActionsStepsLogsResource
from shipyard_airflow.errors import ApiError
from tests.unit.control import common

# Define Global Variables
DATE_ONE = datetime(2018, 4, 5, 16, 29, 11)
DATE_TWO = datetime(2018, 4, 5, 16, 29, 17, 630472)
DATE_THREE = datetime(2018, 4, 5, 16, 29, 21, 984263)
DATE_FOUR = datetime(2018, 4, 5, 16, 29, 13, 698703)
DATE_ONE_STR = DATE_ONE.strftime('%Y-%m-%d %H:%M:%S')
DATE_TWO_STR = DATE_TWO.strftime('%Y-%m-%d %H:%M:%S.%f')
DATE_THREE_STR = DATE_THREE.strftime('%Y-%m-%d %H:%M:%S.%f')
DATE_FOUR_STR = DATE_FOUR.strftime('%Y-%m-%d %H:%M:%S.%f')

EXECUTION_DATE_STR = DATE_ONE.strftime('%Y-%m-%dT%H:%M:%S')

KWARGS = {
    'action_id': '01C9VVQSCFS7V9QB5GBS3WFVSE',
    'step_id': 'action_xcom',
    'try_number': 2
}

ACTIONS_DB = {
    'id': '01C9VVQSCFS7V9QB5GBS3WFVSE',
    'name': 'deploy_site',
    'parameters': {},
    'dag_id': 'deploy_site',
    'dag_execution_date': DATE_ONE_STR,
    'user': 'shipyard',
    'timestamp': DATE_ONE_STR,
    'context_marker': '00c6d78e-fb18-4f55-8a1a-b659a516850d'
}

TASK_INSTANCE_DB = [
    {
        'task_id': 'action_xcom',
        'dag_id': 'deploy_site',
        'execution_date': DATE_ONE,
        'start_date': DATE_TWO,
        'end_date': DATE_THREE,
        'duration': '4.353791',
        'state': 'success',
        'try_number': '1',
        'hostname': 'airflow-worker-0.ucp.svc.cluster.local',
        'unixname': 'airflow',
        'job_id': '2',
        'pool': 'default',
        'priority_weight': '8',
        'operator': 'PythonOperator',
        'queued_dttm': DATE_FOUR,
        'pid': '290',
        'max_tries': '0'
    }, {
        'task_id': 'dag_concurrency_check',
        'dag_id': 'deploy_site',
        'execution_date': DATE_ONE,
        'start_date': DATE_TWO,
        'end_date': DATE_THREE,
        'duration': '4.034112',
        'state': 'success',
        'try_number': '1',
        'hostname': 'airflow-worker-1.ucp.svc.cluster.local',
        'unixname': 'airflow',
        'job_id': '3',
        'pool': 'default',
        'priority_weight': '7',
        'operator': 'ConcurrencyCheckOperator',
        'queued_dttm': DATE_FOUR,
        'pid': '324',
        'max_tries': '0'
    }, {
        'task_id': 'k8s_preflight_check',
        'dag_id': 'deploy_site',
        'execution_date': DATE_ONE,
        'start_date': DATE_TWO,
        'end_date': DATE_THREE,
        'duration': '4.452571',
        'state': 'failed',
        'try_number': '1',
        'hostname': 'airflow-worker-0.ucp.svc.cluster.local',
        'unixname': 'airflow',
        'job_id': '7',
        'pool': 'default',
        'priority_weight': '1',
        'operator': 'K8sHealthCheckOperator',
        'queued_dttm': DATE_FOUR,
        'pid': '394',
        'max_tries': '0'
    }
]

XCOM_RUN_LOGS = """
Running on host airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
Dependencies all met for TaskInstance: deploy_site.action_xcom
Dependencies all met for TaskInstance: deploy_site.action_xcom
INFO -
--------------------------------------------------------------------------------
Starting attempt 1 of 1
--------------------------------------------------------------------------------

Executing Task(PythonOperator): action_xcom
Running: ['bash', '-c', 'airflow tasks run deploy_site action_xcom \
2018-04-11T07:30:37 --job_id 2 --raw -sd DAGS_FOLDER/deploy_site.py']
Running on host airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
Subtask: [2018-04-11 07:30:43,944] {{python_operator.py:90}} \
INFO - Done. Returned value was: None
"""


class TestActionsStepsLogsEndpoint():
    @patch.object(ActionsStepsLogsResource, 'get_action_step_logs',
                  common.str_responder)
    def test_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        # Define Endpoint
        endpoint = "/api/v1.0/actions/{}/steps/{}/logs".format(
            '01C9VVQSCFS7V9QB5GBS3WFVSE',
            'action_xcom')

        result = api_client.simulate_get(endpoint,
                                         headers=common.AUTH_HEADERS)
        assert result.status_code == 200

    @patch('shipyard_airflow.control.helpers.action_helper.ActionsHelper',
           autospec=True)
    def test_generate_log_endpoint(self, mock_actions_helper):
        """Tests log endpoint generation"""
        action_logs_resource = ActionsStepsLogsResource()

        mock_actions_helper.get_formatted_dag_execution_date.return_value = (
            EXECUTION_DATE_STR)
        action_logs_resource.actions_helper = mock_actions_helper

        # Define variables
        action_id = ACTIONS_DB['name']
        step = TASK_INSTANCE_DB[0]
        step_id = TASK_INSTANCE_DB[0]['task_id']
        try_number = '2'
        required_endpoint = (
            'http://airflow-worker-0.ucp.svc.cluster.local:8793/'
            'log/deploy_site/action_xcom/2018-04-05T16:29:11/2.log')

        log_endpoint = action_logs_resource.generate_log_endpoint(
            step, action_id, step_id, try_number)

        assert log_endpoint == required_endpoint

        mock_actions_helper.get_formatted_dag_execution_date.\
            assert_called_once_with(step)

    def _mock_response(
            self,
            status=200,
            text="TEXT"):

        mock_resp = mock.Mock()

        # set status code and content
        mock_resp.status_code = status
        mock_resp.text = text

        return mock_resp

    @mock.patch('requests.get')
    def test_retrieve_logs(self, mock_get):
        """Tests log retrieval"""
        action_logs_resource = ActionsStepsLogsResource()

        # Define variables
        log_endpoint = (
            'http://airflow-worker-0.ucp.svc.cluster.local:8793/'
            'log/deploy_site/action_xcom/2018-04-05T16:29:11/2.log')

        mock_resp = self._mock_response(text=XCOM_RUN_LOGS)
        mock_get.return_value = mock_resp

        result = action_logs_resource.retrieve_logs(log_endpoint)

        assert result == XCOM_RUN_LOGS

    @mock.patch('requests.get')
    def test_retrieve_logs_404(self, mock_get):
        mock_get.return_value.status_code = 404
        action_logs_resource = ActionsStepsLogsResource()
        with pytest.raises(ApiError) as e:
            action_logs_resource.retrieve_logs(None)
        assert ('Airflow endpoint returned error status code' in
                e.value.description)
        assert falcon.HTTP_404 == e.value.status

    @mock.patch('requests.get')
    def test_retrieve_logs_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError
        action_logs_resource = ActionsStepsLogsResource()
        with pytest.raises(ApiError) as e:
            action_logs_resource.retrieve_logs(None)
        assert ("Exception happened during Airflow API request" in
                e.value.description)
        assert falcon.HTTP_500 == e.value.status
