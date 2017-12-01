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
import mock
import pytest

from shipyard_airflow.control.action.actions_id_api import (ActionsIdResource)
from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.policy import ShipyardPolicy
from shipyard_airflow.db.db import AIRFLOW_DB, SHIPYARD_DB
from shipyard_airflow.errors import ApiError
from tests.unit.control.common import create_req, create_resp

DATE_ONE = datetime(2017, 9, 13, 11, 13, 3, 57000)
DATE_TWO = datetime(2017, 9, 13, 11, 13, 5, 57000)
DATE_ONE_STR = DATE_ONE.strftime('%Y-%m-%dT%H:%M:%S')
DATE_TWO_STR = DATE_TWO.strftime('%Y-%m-%dT%H:%M:%S')

context = ShipyardRequestContext()


def actions_db(action_id):
    """
    replaces the actual db call
    """
    return {
        'id': '12345678901234567890123456',
        'name': 'dag_it',
        'parameters': None,
        'dag_id': 'did2',
        'dag_execution_date': DATE_ONE_STR,
        'user': 'robot1',
        'timestamp': DATE_ONE,
        'context_marker': '8-4-4-4-12a'
    }


def dag_runs_db(dag_id, execution_date):
    """
    replaces the actual db call
    """
    return [{
        'dag_id': 'did2',
        'execution_date': DATE_ONE,
        'state': 'FAILED',
        'run_id': '99',
        'external_trigger': 'something',
        'start_date': DATE_ONE,
        'end_date': DATE_ONE
    }]


def tasks_db(dag_id, execution_date):
    """
    replaces the actual db call
    """
    return [{
        'task_id': '1a',
        'dag_id': 'did2',
        'execution_date': DATE_ONE,
        'state': 'SUCCESS',
        'run_id': '12345',
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
        'execution_date': DATE_ONE,
        'state': 'SUCCESS',
        'run_id': '12345',
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
        'execution_date': DATE_ONE,
        'state': 'FAILED',
        'run_id': '12345',
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
    mock_get_action.assert_called_once_with(kwargs['action_id'])
    assert resp.body == '"action_returned"'
    assert resp.status == '200 OK'


def test_get_action_success():
    """
    Tests the main response from get all actions
    """
    action_resource = ActionsIdResource()
    # stubs for db
    action_resource.get_action_db = actions_db
    action_resource.get_dag_run_db = dag_runs_db
    action_resource.get_tasks_db = tasks_db
    action_resource.get_validations_db = get_validations
    action_resource.get_action_command_audit_db = get_ac_audit

    action = action_resource.get_action('12345678901234567890123456')
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
        action_resource.get_action(action_id)
    assert action_id in str(expected_exc)
    assert 'Action not found' in str(expected_exc)


@mock.patch.object(ActionsIdResource, 'get_dag_run_db', return_value=None)
def test_get_dag_run_by_id_empty(mock_get_dag_run_db):
    '''test that an empty dag_run_list will return None'''
    action_resource = ActionsIdResource()
    context.policy_engine = ShipyardPolicy()
    dag_id = 'test_dag_id'
    execution_date = 'test_execution_date'
    result = action_resource.get_dag_run_by_id(dag_id, execution_date)
    mock_get_dag_run_db.assert_called_once_with(dag_id, execution_date)
    assert result is None


def test_get_dag_run_by_id_notempty():
    '''test that a nonempty dag_run_list will return the 1st dag in the list'''
    action_resource = ActionsIdResource()
    action_resource.get_dag_run_db = dag_runs_db
    dag_id = 'test_dag_id'
    execution_date = 'test_execution_date'
    result = action_resource.get_dag_run_by_id(dag_id, execution_date)
    assert result == {
        'dag_id': 'did2',
        'execution_date': DATE_ONE,
        'state': 'FAILED',
        'run_id': '99',
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


@mock.patch.object(AIRFLOW_DB, 'get_tasks_by_id')
def test_get_tasks_db(mock_get_tasks_by_id):
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

    result = action_resource.get_tasks_db(dag_id, execution_date)
    mock_get_tasks_by_id.assert_called_once_with(
        dag_id=dag_id, execution_date=execution_date)
    assert result == expected


@mock.patch.object(AIRFLOW_DB, 'get_dag_runs_by_id')
def test_get_dag_run_db(mock_get_dag_runs_by_id):
    expected = {
        'dag_id': 'did2',
        'execution_date': DATE_ONE,
        'state': 'FAILED',
        'run_id': '99',
        'external_trigger': 'something',
        'start_date': DATE_ONE,
        'end_date': DATE_ONE
    }
    mock_get_dag_runs_by_id.return_value = expected
    action_resource = ActionsIdResource()
    dag_id = 'test_dag_id'
    execution_date = 'test_execution_date'

    result = action_resource.get_dag_run_db(dag_id, execution_date)
    mock_get_dag_runs_by_id.assert_called_once_with(
        dag_id=dag_id, execution_date=execution_date)
    assert result == expected


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
