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
from shipyard_airflow.control.actions_control_api import ActionsControlResource
from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.db.errors import AirflowStateError
from shipyard_airflow.db.db import AIRFLOW_DB
from shipyard_airflow.errors import ApiError


def actions_db(action_id):
    """
    replaces the actual db call
    """
    if action_id == 'not found':
        return None
    elif action_id == 'state error':
        return {
            'id': 'state error',
            'name': 'dag_it',
            'parameters': None,
            'dag_id': 'state error',
            'dag_execution_date': '2017-09-06 14:10:08.528402',
            'user': 'robot1',
            'timestamp': '2017-09-06 14:10:08.528402',
            'context_marker': '8-4-4-4-12a'
        }
    else:
        return {
            'id': '59bb330a-9e64-49be-a586-d253bb67d443',
            'name': 'dag_it',
            'parameters': None,
            'dag_id': 'did2',
            'dag_execution_date': '2017-09-06 14:10:08.528402',
            'user': 'robot1',
            'timestamp': '2017-09-06 14:10:08.528402',
            'context_marker': '8-4-4-4-12a'
        }


def control_dag_run(dag_id,
                    execution_date,
                    expected_state,
                    desired_state):
    if dag_id == 'state error':
        raise AirflowStateError(message='test error')
    else:
        pass


def audit_control_command_db(action_audit):
    pass


def test_get_action():
    """
    Tests the main response from get all actions
    """
    saved_control_dag_run = AIRFLOW_DB._control_dag_run
    try:
        action_resource = ActionsControlResource()
        # stubs for db
        action_resource.get_action_db = actions_db
        action_resource.audit_control_command_db = audit_control_command_db

        AIRFLOW_DB._control_dag_run = control_dag_run

        # bad action
        try:
            action_resource.handle_control(
                action_id='not found',
                control_verb='meep',
                context=ShipyardRequestContext()
            )
            assert False, "shouldn't find the action"
        except ApiError as api_error:
            assert api_error.title == 'Action not found'
            assert api_error.status == '404 Not Found'

        # bad control
        try:
            action_resource.handle_control(
                action_id='59bb330a-9e64-49be-a586-d253bb67d443',
                control_verb='meep',
                context=ShipyardRequestContext()
            )
            assert False, 'meep is not a valid action'
        except ApiError as api_error:
            assert api_error.title == 'Control not supported'
            assert api_error.status == '404 Not Found'

        # success on each action - pause, unpause, stop
        try:
            action_resource.handle_control(
                action_id='59bb330a-9e64-49be-a586-d253bb67d443',
                control_verb='pause',
                context=ShipyardRequestContext()
            )
        except ApiError as api_error:
            assert False, 'Should not raise an ApiError'

        try:
            action_resource.handle_control(
                action_id='59bb330a-9e64-49be-a586-d253bb67d443',
                control_verb='unpause',
                context=ShipyardRequestContext()
            )
        except ApiError as api_error:
            assert False, 'Should not raise an ApiError'

        try:
            action_resource.handle_control(
                action_id='59bb330a-9e64-49be-a586-d253bb67d443',
                control_verb='stop',
                context=ShipyardRequestContext()
            )
        except ApiError as api_error:
            assert False, 'Should not raise an ApiError'

        # pause state conflict
        try:
            action_resource.handle_control(
                action_id='state error',
                control_verb='pause',
                context=ShipyardRequestContext()
            )
            assert False, 'should raise a conflicting state'
        except ApiError as api_error:
            assert api_error.title == 'Unable to pause action'
            assert api_error.status == '409 Conflict'

        # Unpause state conflict
        try:
            action_resource.handle_control(
                action_id='state error',
                control_verb='unpause',
                context=ShipyardRequestContext()
            )
            assert False, 'should raise a conflicting state'
        except ApiError as api_error:
            assert api_error.title == 'Unable to unpause action'
            assert api_error.status == '409 Conflict'

        # Stop state conflict
        try:
            action_resource.handle_control(
                action_id='state error',
                control_verb='stop',
                context=ShipyardRequestContext()
            )
            assert False, 'should raise a conflicting state'
        except ApiError as api_error:
            assert api_error.title == 'Unable to stop action'
            assert api_error.status == '409 Conflict'
    finally:
        # modified class variable... replace it
        AIRFLOW_DB._control_dag_run = saved_control_dag_run
