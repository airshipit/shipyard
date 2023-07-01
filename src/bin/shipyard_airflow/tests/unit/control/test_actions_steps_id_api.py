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
from datetime import datetime
from unittest.mock import patch

import pytest

from shipyard_airflow.common.notes.notes import NotesManager
from shipyard_airflow.common.notes.notes_helper import NotesHelper
from shipyard_airflow.common.notes.storage_impl_mem import (
    MemoryNotesStorage
)
from shipyard_airflow.control.action.actions_steps_id_api import \
    ActionsStepsResource
from shipyard_airflow.errors import ApiError
from tests.unit.control import common

RUN_ID_ONE = "AAAAAAAAAAAAAAAAAAAAA"
RUN_ID_TWO = "BBBBBBBBBBBBBBBBBBBBB"
DATE_ONE = datetime(2017, 9, 13, 11, 13, 3, 57000)
DATE_TWO = datetime(2017, 9, 13, 11, 13, 5, 57000)
DATE_ONE_STR = DATE_ONE.strftime('%Y-%m-%dT%H:%M:%S')
DATE_TWO_STR = DATE_TWO.strftime('%Y-%m-%dT%H:%M:%S')


def get_token():
    """Stub method to use for NotesHelper/NotesManager"""
    return "token"

# Notes helper that can be mocked into various objects to prevent database
# dependencies
nh = NotesHelper(NotesManager(MemoryNotesStorage(), get_token))


def actions_db(action_id):
    """
    replaces the actual db call
    """
    return {
        'id': '59bb330a-9e64-49be-a586-d253bb67d443',
        'name': 'dag_it',
        'parameters': None,
        'dag_id': 'did2',
        'dag_execution_date': DATE_ONE_STR,
        'user': 'robot1',
        'timestamp': DATE_ONE_STR,
        'context_marker': '8-4-4-4-12a'
    }


def tasks_db(dag_id, execution_date):
    """
    replaces the actual db call
    """
    return [{
        'task_id': '1a',
        'dag_id': 'did2',
        # 'execution_date': DATE_ONE,
        'state': 'SUCCESS',
        'run_id': RUN_ID_ONE,
        'external_trigger': 'something',
        'start_date': DATE_ONE,
        'end_date': DATE_ONE,
        'duration': '20mins',
        'try_number': '1',
        'operator': 'smooth',
        'queued_dttm': DATE_ONE
    }, {
        'task_id': '1b',
        'dag_id': 'did2',
        # 'execution_date': DATE_ONE,
        'state': 'SUCCESS',
        'run_id': RUN_ID_ONE,
        'external_trigger': 'something',
        'start_date': DATE_TWO,
        'end_date': DATE_TWO,
        'duration': '1minute',
        'try_number': '1',
        'operator': 'smooth',
        'queued_dttm': DATE_ONE
    }, {
        'task_id': '1c',
        'dag_id': 'did2',
        # 'execution_date': DATE_ONE,
        'state': 'FAILED',
        'run_id': RUN_ID_ONE,
        'external_trigger': 'something',
        'start_date': DATE_TWO,
        'end_date': DATE_TWO,
        'duration': '1day',
        'try_number': '3',
        'operator': 'smooth',
        'queued_dttm': DATE_TWO
    }]


class TestActionsStepsResource():
    @patch.object(ActionsStepsResource, 'get_action_step',
                  common.str_responder)
    def test_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        result = api_client.simulate_get(
            "/api/v1.0/actions/123456/steps/123456",
            headers=common.AUTH_HEADERS)
        assert result.status_code == 200

    @patch('shipyard_airflow.control.helpers.action_helper.notes_helper',
           new=nh)
    @patch('shipyard_airflow.control.action.actions_steps_id_api.notes_helper',
           new=nh)
    def test_get_action_step_success(self, *args):
        """Tests the main response from get all actions"""
        action_resource = ActionsStepsResource()
        # stubs for db
        action_resource.get_action_db = actions_db
        action_resource.get_tasks_db = tasks_db

        step = action_resource.get_action_step(
            '59bb330a-9e64-49be-a586-d253bb67d443', '1c')
        assert step['index'] == 3
        assert step['try_number'] == '3'
        assert step['operator'] == 'smooth'

    def test_get_action_step_error_action(self):
        """Validate ApiError, 'Action not found' is raised"""
        action_resource = ActionsStepsResource()
        with patch.object(ActionsStepsResource,
                          'get_action_db') as mock_method:
            mock_method.return_value = None
            with pytest.raises(ApiError) as api_error:
                action_resource.get_action_step(
                    '59bb330a-9e64-49be-a586-d253bb67d443', 'cheese')
            assert 'Action not found' in str(api_error)

    @patch('shipyard_airflow.control.helpers.action_helper.notes_helper',
           new=nh)
    @patch('shipyard_airflow.control.action.actions_steps_id_api.notes_helper',
           new=nh)
    def test_get_action_step_error_step(self):
        """Validate ApiError, 'Step not found' is raised"""
        action_resource = ActionsStepsResource()
        # stubs for db
        action_resource.get_action_db = actions_db
        action_resource.get_tasks_db = tasks_db

        with pytest.raises(ApiError) as api_error:
            step = action_resource.get_action_step(
                '59bb330a-9e64-49be-a586-d253bb67d443', 'cheese')
        assert 'Step not found' in str(api_error)

    @patch('shipyard_airflow.db.shipyard_db.ShipyardDbAccess.get_action_by_id')
    def test_get_action_db(self, mock_get_action_by_id):
        action_resource = ActionsStepsResource()
        action_id = '123456789'
        action_resource.get_action_db(action_id)
        mock_get_action_by_id.assert_called_with(action_id=action_id)

    @patch('shipyard_airflow.db.airflow_db.AirflowDbAccess.get_tasks_by_id')
    def test_get_tasks_db(self, mock_get_tasks_by_id):
        action_resource = ActionsStepsResource()
        dag_id = '123456'
        execution_date = DATE_ONE
        action_resource.get_tasks_db(dag_id, execution_date)
        mock_get_tasks_by_id.assert_called_with(
            dag_id=dag_id, execution_date=execution_date)

