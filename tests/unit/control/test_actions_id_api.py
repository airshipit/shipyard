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
import json

from shipyard_airflow.control.action.actions_id_api import (ActionsIdResource)

DATE_ONE = datetime(2017, 9, 13, 11, 13, 3, 57000)
DATE_TWO = datetime(2017, 9, 13, 11, 13, 5, 57000)
DATE_ONE_STR = DATE_ONE.strftime('%Y-%m-%dT%H:%M:%S')
DATE_TWO_STR = DATE_TWO.strftime('%Y-%m-%dT%H:%M:%S')


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
    return [
        {
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
        },
        {
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
        },
        {
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
        }
    ]


def get_validations(action_id):
    """
    Stub to return validations
    """
    return [
        {
            'id': '43',
            'action_id': '12345678901234567890123456',
            'validation_name': 'It has shiny goodness',
            'details': 'This was not very shiny.'
        }
    ]


def get_ac_audit(action_id):
    """
    Stub to return command audit response
    """
    return [
        {
            'id': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'action_id': '12345678901234567890123456',
            'command': 'PAUSE',
            'user': 'Operator 99',
            'datetime': DATE_ONE
        },
        {
            'id': 'ABCDEFGHIJKLMNOPQRSTUVWXYA',
            'action_id': '12345678901234567890123456',
            'command': 'UNPAUSE',
            'user': 'Operator 99',
            'datetime': DATE_TWO
        }
    ]


def test_get_action():
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
    print(json.dumps(action, default=str))
    if action['name'] == 'dag_it':
        assert len(action['steps']) == 3
        assert action['dag_status'] == 'FAILED'
        assert len(action['command_audit']) == 2
