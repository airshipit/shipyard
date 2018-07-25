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
from unittest.mock import patch

import pytest

from shipyard_airflow.control.action.actions_validations_id_api import \
    ActionsValidationsResource
from shipyard_airflow.errors import ApiError
from tests.unit.control import common


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


class TestActionsValidationsResource():
    @patch.object(ActionsValidationsResource, 'get_action_validation',
                  common.str_responder)
    def test_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        result = api_client.simulate_get(
            "/api/v1.0/actions/123456/validations/123456",
            headers=common.AUTH_HEADERS)
        assert result.status_code == 200

    def test_get_action_validation(self):
        """Tests the main response from get all actions"""
        action_resource = ActionsValidationsResource()
        # stubs for db
        action_resource.get_action_db = actions_db
        action_resource.get_validation_db = get_validations

        validation = action_resource.get_action_validation(
            action_id='59bb330a-9e64-49be-a586-d253bb67d443',
            validation_id='43')
        assert validation[
            'action_id'] == '59bb330a-9e64-49be-a586-d253bb67d443'
        assert validation['validation_name'] == 'It has shiny goodness'

        with pytest.raises(ApiError) as api_error:
            action_resource.get_action_validation(
                action_id='59bb330a-9e64-49be-a586-d253bb67d443',
                validation_id='not a chance')
        assert 'Validation not found' in str(api_error)

        with pytest.raises(ApiError) as api_error:
            validation = action_resource.get_action_validation(
                action_id='error_it', validation_id='not a chance')
        assert 'Action not found' in str(api_error)

    @patch('shipyard_airflow.db.shipyard_db.ShipyardDbAccess.get_action_by_id')
    def test_get_action_db(self, mock_get_action_by_id):
        action_resource = ActionsValidationsResource()
        action_id = '123456789'
        action_resource.get_action_db(action_id)
        mock_get_action_by_id.assert_called_with(action_id=action_id)

    @patch(
        'shipyard_airflow.db.shipyard_db.ShipyardDbAccess.get_validation_by_id'
    )
    def test_get_validation_db(self, mock_get_tasks_by_id):
        action_resource = ActionsValidationsResource()
        validation_id = '123456'
        action_resource.get_validation_db(validation_id)
        mock_get_tasks_by_id.assert_called_with(validation_id=validation_id)
