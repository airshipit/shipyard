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
import json
import os
from datetime import datetime

from shipyard_airflow.control.actions_api import ActionsResource
from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.errors import ApiError

DATE_ONE = datetime(2017, 9, 13, 11, 13, 3, 57000)
DATE_TWO = datetime(2017, 9, 13, 11, 13, 5, 57000)
DATE_ONE_STR = DATE_ONE.strftime('%Y-%m-%dT%H:%M:%S')
DATE_TWO_STR = DATE_TWO.strftime('%Y-%m-%dT%H:%M:%S')


def actions_db():
    """
    replaces the actual db call
    """
    return [
        {
            'id': 'aaaaaa',
            'name': 'dag_it',
            'parameters': None,
            'dag_id': 'did1',
            'dag_execution_date': DATE_ONE_STR,
            'user': 'robot1',
            'timestamp': DATE_ONE,
            'context_marker': '8-4-4-4-12a'
        },
        {
            'id': 'bbbbbb',
            'name': 'dag2',
            'parameters': {
                'p1': 'p1val'
            },
            'dag_id': 'did2',
            'dag_execution_date': DATE_ONE_STR,
            'user': 'robot2',
            'timestamp': DATE_ONE,
            'context_marker': '8-4-4-4-12b'
        },
    ]


def dag_runs_db():
    """
    replaces the actual db call
    """
    return [
        {
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO
        },
        {
            'dag_id': 'did1',
            'execution_date': DATE_ONE,
            'state': 'FAILED',
            'run_id': '99',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_ONE
        },
    ]


def tasks_db():
    """
    replaces the actual db call
    """
    return [
        {
            'task_id': '1a',
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO,
            'duration': '20mins',
            'try_number': '1',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
        {
            'task_id': '1b',
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO,
            'duration': '1minute',
            'try_number': '1',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
        {
            'task_id': '1c',
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO,
            'duration': '1day',
            'try_number': '3',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
        {
            'task_id': '2a',
            'dag_id': 'did1',
            'execution_date': DATE_ONE,
            'state': 'FAILED',
            'start_date': DATE_ONE,
            'end_date': DATE_ONE,
            'duration': '1second',
            'try_number': '2',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
    ]

def airflow_stub(**kwargs):
    """
    asserts that the airflow invocation method was called with the right
    parameters
    """
    assert kwargs['dag_id']
    assert kwargs['action']
    print(kwargs)
    return '2017-09-06 14:10:08.528402'

def insert_action_stub(**kwargs):
    """
    asserts that the insert action was called with the right parameters
    """
    assert kwargs['action']

def audit_control_command_db(action_audit):
    """
    Stub for inserting the invoke record
    """
    assert action_audit['command'] == 'invoke'


context = ShipyardRequestContext()

def test_get_all_actions():
    """
    Tests the main response from get all actions
    """
    action_resource = ActionsResource()
    action_resource.get_all_actions_db = actions_db
    action_resource.get_all_dag_runs_db = dag_runs_db
    action_resource.get_all_tasks_db = tasks_db
    os.environ['DB_CONN_AIRFLOW'] = 'nothing'
    os.environ['DB_CONN_SHIPYARD'] = 'nothing'
    result = action_resource.get_all_actions()
    print(result)
    assert len(result) == len(actions_db())
    for action in result:
        if action['name'] == 'dag_it':
            assert len(action['steps']) == 1
            assert action['dag_status'] == 'FAILED'
        if action['name'] == 'dag2':
            assert len(action['steps']) == 3
            assert action['dag_status'] == 'SUCCESS'

def test_create_action():
    action_resource = ActionsResource()
    action_resource.get_all_actions_db = actions_db
    action_resource.get_all_dag_runs_db = dag_runs_db
    action_resource.get_all_tasks_db = tasks_db
    action_resource.invoke_airflow_dag = airflow_stub
    action_resource.insert_action = insert_action_stub
    action_resource.audit_control_command_db = audit_control_command_db

    # with invalid input. fail.
    try:
        action = action_resource.create_action(
            action={'name': 'broken', 'parameters': {'a': 'aaa'}},
            context=context
        )
        assert False, 'Should throw an ApiError'
    except ApiError:
        # expected
        pass

    # with valid input and some parameters
    try:
        action = action_resource.create_action(
            action={'name': 'deploy_site', 'parameters': {'a': 'aaa'}},
            context=context
        )
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
    except ApiError:
        assert False, 'Should not raise an ApiError'
    print(json.dumps(action, default=str))

    # with valid input and no parameters
    try:
        action = action_resource.create_action(
            action={'name': 'deploy_site'},
            context=context
        )
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
    except ApiError:
        assert False, 'Should not raise an ApiError'
    print(json.dumps(action, default=str))
