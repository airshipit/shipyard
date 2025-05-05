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
from unittest import mock

import pytest

from shipyard_airflow.common.notes.notes import NotesManager
from shipyard_airflow.common.notes.notes_helper import NotesHelper
from shipyard_airflow.common.notes.storage_impl_mem import (
    MemoryNotesStorage
)
from shipyard_airflow.control.action.actions_id_api import (ActionsIdResource)
from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.policy import ShipyardPolicy
from shipyard_airflow.db.db import SHIPYARD_DB
from shipyard_airflow.api.api import AIRFLOW_API
from shipyard_airflow.errors import ApiError
from tests.unit.control.common import create_req, create_resp

RUN_ID_ONE = "AAAAAAAAAAAAAAAAAAAAA"
RUN_ID_TWO = "BBBBBBBBBBBBBBBBBBBBB"
DATE_ONE = datetime(2017, 9, 13, 11, 13, 3, 57000)
DATE_TWO = datetime(2017, 9, 13, 11, 13, 5, 57000)
DATE_ONE_STR = DATE_ONE.strftime('%Y-%m-%dT%H:%M:%S')
DATE_TWO_STR = DATE_TWO.strftime('%Y-%m-%dT%H:%M:%S')

context = ShipyardRequestContext()


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
        'id': RUN_ID_ONE,
        'name': 'dag_it',
        'parameters': None,
        'dag_id': 'did1',
        'dag_execution_date': DATE_ONE_STR,
        'user': 'robot1',
        'timestamp': DATE_ONE,
        'context_marker': '8-4-4-4-12a',
        'steps': [1, 2, 3],
        'dag_status': 'FAILED',
        'command_audit': [1, 2]
    }


def dag_runs_api(dag_id, execution_date):
    """
    replaces the actual api call
    """
    return [{
        'dag_id': 'did2',
        'execution_date': DATE_ONE,
        'state': 'FAILED',
        'run_id': RUN_ID_TWO,
        'external_trigger': 'something',
        'start_date': DATE_ONE,
        'end_date': DATE_ONE
    }]


def tasks_api(dag_id, execution_date):
    """
    replaces the actual db call
    """
    return [{
        'task_id': '1a',
        'dag_id': 'did2',
        'state': 'SUCCESS',
        'run_id': RUN_ID_TWO,
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
        'state': 'SUCCESS',
        'run_id': RUN_ID_TWO,
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
        'state': 'FAILED',
        'run_id': RUN_ID_TWO,
        'external_trigger': 'something',
        'start_date': DATE_TWO,
        'end_date': DATE_TWO,
        'duration': '1day',
        'try_number': '3',
        'operator': 'smooth',
        'queued_dttm': DATE_TWO
    }]


def get_validations(action_id):
    """
    Stub to return validations
    """
    return [{
        'id': '43',
        'action_id': '12345678901234567890123456',
        'validation_name': 'It has shiny goodness',
        'details': 'This was not very shiny.'
    }]


def get_ac_audit(action_id):
    """
    Stub to return command audit response
    """
    return [{
        'id': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'action_id': '12345678901234567890123456',
        'command': 'PAUSE',
        'user': 'Operator 99',
        'datetime': DATE_ONE
    }, {
        'id': 'ABCDEFGHIJKLMNOPQRSTUVWXYA',
        'action_id': '12345678901234567890123456',
        'command': 'UNPAUSE',
        'user': 'Operator 99',
        'datetime': DATE_TWO
    }]


@mock.patch.object(
    ActionsIdResource, 'get_action', return_value='action_returned')
@mock.patch.object(ShipyardPolicy, 'authorize', return_value=True)
def test_on_get(mock_authorize, mock_get_action):
    action_resource = ActionsIdResource()
    context.policy_engine = ShipyardPolicy()
    kwargs = {'action_id': None}
    req = create_req(context, None)
    resp = create_resp()
    action_resource.on_get(req, resp, **kwargs)
    mock_authorize.assert_called_once_with('workflow_orchestrator:get_action',
                                           context)
    mock_get_action.assert_called_once_with(action_id=None, verbosity=1)
    assert resp.text == '"action_returned"'
    assert resp.status == '200 OK'


@mock.patch("requests.get")
@mock.patch("requests.post")
@mock.patch('shipyard_airflow.control.helpers.action_helper.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.control.action.actions_id_api.notes_helper',
            new=nh)
def test_get_action_success(*args):
    """
    Tests the main response from get all actions
    """
    action_resource = ActionsIdResource()
    # stubs for db
    action_resource.get_action_db = actions_db
    action_resource.get_dag_run_api = dag_runs_api
    action_resource.get_tasks_api = tasks_api
    action_resource.get_validations_db = get_validations
    action_resource.get_action_command_audit_db = get_ac_audit

    action = action_resource.get_action(
        action_id='12345678901234567890123456',
        verbosity=1
    )
    if action['name'] == 'dag_it':
        assert len(action['steps']) == 3
        assert action['dag_status'] == 'FAILED'
        assert len(action['command_audit']) == 2


@mock.patch.object(ActionsIdResource, 'get_action_db', return_value=None)
def test_get_action_errors(mock_get_action):
    '''verify when get_action_db returns None, ApiError is raised'''
    action_resource = ActionsIdResource()
    action_id = '12345678901234567890123456'

    with pytest.raises(ApiError) as expected_exc:
        action_resource.get_action(action_id=action_id, verbosity=1)
    assert action_id in str(expected_exc)
    assert 'Action not found' in str(expected_exc)


@mock.patch.object(ActionsIdResource, 'get_dag_run_api', return_value=None)
def test_get_dag_runs_by_id_empty(mock_get_dag_run_api):
    '''test that an empty dag_run_list will return None'''
    action_resource = ActionsIdResource()
    context.policy_engine = ShipyardPolicy()
    dag_id = 'test_dag_id'
    execution_date = 'test_execution_date'
    result = action_resource.get_dag_runs_by_id(dag_id, execution_date)
    mock_get_dag_run_api.assert_called_once_with(dag_id, execution_date)
    assert result is None

@mock.patch("requests.get")
def test_get_dag_runs_by_id_notempty(mock_get):
    action_resource = ActionsIdResource()
    action_resource.get_dag_run_api = dag_runs_api
    dag_id = 'test_dag_id'
    execution_date = 'test_execution_date'
    result = action_resource.get_dag_runs_by_id(dag_id, execution_date)
    assert result == {
        'dag_id': 'did2',
        'execution_date': DATE_ONE,  # или DATE_ONE_STR, если везде строки
        'state': 'FAILED',
        'run_id': RUN_ID_TWO,
        'external_trigger': 'something',
        'start_date': DATE_ONE,
        'end_date': DATE_ONE
    }


@mock.patch.object(
    SHIPYARD_DB,
    'get_action_by_id', )
def test_get_action_db(mock_get_action_by_id):
    expected = {
        'id': '12345678901234567890123456',
        'name': 'dag_it',
        'parameters': None,
        'dag_id': 'did2',
        'dag_execution_date': DATE_ONE_STR,
        'user': 'robot1',
        'timestamp': DATE_ONE,
        'context_marker': '8-4-4-4-12a'
    }
    mock_get_action_by_id.return_value = expected
    action_resource = ActionsIdResource()
    action_id = 'test_action_id'

    result = action_resource.get_action_db(action_id)
    mock_get_action_by_id.assert_called_once_with(action_id=action_id)
    assert result == expected


@mock.patch.object(SHIPYARD_DB, 'get_validation_by_action_id')
def test_get_validations_db(mock_get_validation_by_action_id):
    expected = {
        'id': '43',
        'action_id': '12345678901234567890123456',
        'validation_name': 'It has shiny goodness',
        'details': 'This was not very shiny.'
    }
    mock_get_validation_by_action_id.return_value = expected
    action_resource = ActionsIdResource()
    action_id = 'test_action_id'

    result = action_resource.get_validations_db(action_id)
    mock_get_validation_by_action_id.assert_called_once_with(
        action_id=action_id)
    assert result == expected


@mock.patch.object(AIRFLOW_API, 'get_tasks_by_id')
def test_get_tasks_api(mock_get_tasks_by_id):
    expected = {
        'id': '43',
        'action_id': '12345678901234567890123456',
        'validation_name': 'It has shiny goodness',
        'details': 'This was not very shiny.'
    }
    mock_get_tasks_by_id.return_value = expected
    action_resource = ActionsIdResource()
    dag_id = 'test_dag_id'
    execution_date = 'test_execution_date'

    result = action_resource.get_tasks_api(dag_id, execution_date)
    mock_get_tasks_by_id.assert_called_once_with(
        dag_id=dag_id, execution_date=execution_date)
    assert result == expected

@mock.patch("requests.post")
def test_get_dag_run_api(mock_post):
    # Мокаем ответ Airflow API на POST /dagRuns/list
    mock_post.return_value = mock.Mock(
        status_code=200,
        json=mock.Mock(return_value={
            'dag_runs': [
                {
                    "dag_run_id": "run_123",
                    "dag_id": "test_dag_id",
                    "state": "success",
                    "logical_date": "2017-09-13T11:13:03",
                    "execution_date": "2017-09-13T11:13:03",
                    "run_type": "manual",
                    "external_trigger": True,
                    "conf": {"foo": "bar"},
                    "end_date": "2024-01-01T01:00:00+00:00",
                    "start_date": "2024-01-01T00:00:00+00:00"
                }
            ]
        }),
        raise_for_status=mock.Mock()
    )

    action_resource = ActionsIdResource()
    dag_id = "test_dag_id"
    execution_date = "2017-09-13T11:13:03"
    result = action_resource.get_dag_run_api(dag_id, execution_date)

    assert isinstance(result, list)
    assert len(result) == 1
    dag_run = result[0]
    assert dag_run["dag_id"] == "test_dag_id"
    assert dag_run["execution_date"] == "2017-09-13T11:13:03"
    assert dag_run["state"] == "success"
    assert dag_run["run_id"] == "run_123"
    assert dag_run["external_trigger"] is True
    assert dag_run["conf"] == {"foo": "bar"}
    assert dag_run["start_date"] == "2024-01-01T00:00:00+00:00"
    assert dag_run["end_date"] == "2024-01-01T01:00:00+00:00"

@mock.patch.object(SHIPYARD_DB, 'get_command_audit_by_action_id')
def test_get_action_command_audit_db(mock_get_command_audit_by_action_id):
    expected = {
        'id': '12345678901234567890123456',
        'name': 'dag_it',
        'parameters': None,
        'dag_id': 'did2',
        'dag_execution_date': DATE_ONE_STR,
        'user': 'robot1',
        'timestamp': DATE_ONE,
        'context_marker': '8-4-4-4-12a'
    }
    mock_get_command_audit_by_action_id.return_value = expected
    action_resource = ActionsIdResource()
    action_id = 'test_action_id'

    result = action_resource.get_action_command_audit_db(action_id)
    mock_get_command_audit_by_action_id.assert_called_once_with(action_id)
    assert result == expected
