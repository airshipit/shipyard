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
import falcon

from shipyard_airflow import policy
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.db.db import SHIPYARD_DB
from shipyard_airflow.errors import ApiError


# /api/v1.0/actions/{action_id}/validations/{validation_id}
class ActionsValidationsResource(BaseResource):
    """
    The actions validations resource is the validtions of an action
    """

    @policy.ApiEnforcer(policy.GET_ACTION_VALIDATION)
    def on_get(self, req, resp, **kwargs):
        """
        Return validation details for an action validation
        :returns: a json object describing a validation
        """
        resp.text = self.to_json(
            self.get_action_validation(kwargs['action_id'],
                                       kwargs['validation_id']))
        resp.status = falcon.HTTP_200

    def get_action_validation(self, action_id, validation_id):
        """
        Interacts with the shipyard database to return the requested
        validation information
        :returns: the validation dicitonary object
        """
        action = self.get_action_db(action_id=action_id)

        if action is None:
            raise ApiError(title='Action not found',
                           description='Unknown action {}'.format(action_id),
                           status=falcon.HTTP_404)

        validation = self.get_validation_db(validation_id=validation_id)
        if validation is not None:
            return validation

        # if we didn't find it, 404
        raise ApiError(
            title='Validation not found',
            description='Unknown validation {}'.format(validation_id),
            status=falcon.HTTP_404)

    def get_action_db(self, action_id):
        """
        Wrapper for call to the shipyard database to get an action
        :returns: a dictionary of action details.
        """
        return SHIPYARD_DB.get_action_by_id(action_id=action_id)

    def get_validation_db(self, validation_id):
        """
        Wrapper for call to the shipyard database to get an action
        :returns: a dictionary of action details.
        """
        return SHIPYARD_DB.get_validation_by_id(validation_id=validation_id)
