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
from shipyard_airflow.control.actions_validations_id_api import (
    ActionsValidationsResource
)
from shipyard_airflow.errors import ApiError


def actions_db(action_id):
    """
    replaces the actual db call
    """
    if action_id == 'error_it':
        return None
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


def get_validations(validation_id):
    """
    Stub to return validations
    """
    if validation_id == '43':
        return {
            'id': '43',
            'action_id': '59bb330a-9e64-49be-a586-d253bb67d443',
            'validation_name': 'It has shiny goodness',
            'details': 'This was not very shiny.'
        }
    else:
        return None


def test_get_action_validation():
    """
    Tests the main response from get all actions
    """
    action_resource = ActionsValidationsResource()
    # stubs for db
    action_resource.get_action_db = actions_db
    action_resource.get_validation_db = get_validations

    validation = action_resource.get_action_validation(
        action_id='59bb330a-9e64-49be-a586-d253bb67d443',
        validation_id='43'
    )
    print(json.dumps(validation, default=str))
    assert validation['action_id'] == '59bb330a-9e64-49be-a586-d253bb67d443'
    assert validation['validation_name'] == 'It has shiny goodness'

    try:
        validation = action_resource.get_action_validation(
            action_id='59bb330a-9e64-49be-a586-d253bb67d443',
            validation_id='not a chance'
        )
        assert False
    except ApiError as api_error:
        assert api_error.status == '404 Not Found'
        assert api_error.title == 'Validation not found'

    try:
        validation = action_resource.get_action_validation(
            action_id='error_it',
            validation_id='not a chance'
        )
        assert False
    except ApiError as api_error:
        assert api_error.status == '404 Not Found'
        assert api_error.title == 'Action not found'
