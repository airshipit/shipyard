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
import ulid

from shipyard_airflow import policy
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.db.db import AIRFLOW_DB, SHIPYARD_DB
from shipyard_airflow.db.errors import AirflowStateError
from shipyard_airflow.errors import ApiError


# /api/v1.0/actions/{action_id}/control/{control_verb}
class ActionsControlResource(BaseResource):
    """
    The actions control resource allows for runtime control
    """
    def __init__(self):
        BaseResource.__init__(self)
        self.controls = {
            'pause': self.pause_dag,
            'unpause': self.unpause_dag,
            'stop': self.stop_dag
        }

    @policy.ApiEnforcer(policy.INVOKE_ACTION_CONTROL)
    def on_post(self, req, resp, **kwargs):
        """
        Returns that a control was recevied (202 response)
        :returns: a no-body response
        """
        self.handle_control(kwargs['action_id'],
                            kwargs['control_verb'],
                            req.context)
        resp.status = falcon.HTTP_202

    def handle_control(self, action_id, control_verb, context):
        """
        Interacts with airflow to trigger a dag control
        :returns: nothing
        """
        action = self.get_action_db(action_id=action_id)

        if action is None:
            raise ApiError(
                title='Action not found',
                description='Unknown action {}'.format(action_id),
                status=falcon.HTTP_404)

        if control_verb in self.controls:
            self.controls.get(control_verb)(
                dag_id=action['dag_id'],
                execution_date=action['dag_execution_date'])
            self.audit_control_command_db({
                'id': ulid.ulid(),
                'action_id': action_id,
                'command': control_verb,
                'user': context.user
            })
        else:
            raise ApiError(
                title='Control not supported',
                description='Unknown control {}'.format(control_verb),
                status=falcon.HTTP_404)

    def get_action_db(self, action_id):
        """
        Wrapper for call to the shipyard database to get an action
        :returns: a dictionary of action details.
        """
        return SHIPYARD_DB.get_action_by_id(
            action_id=action_id)

    def audit_control_command_db(self, action_audit):
        """
        Wrapper for the shipyard db call to record an audit of the
        action control taken
        """
        return SHIPYARD_DB.insert_action_command_audit(action_audit)

    def pause_dag(self, dag_id, execution_date):
        """
        Sets the pause flag on this dag/execution
        """
        try:
            AIRFLOW_DB.pause_dag_run(
                dag_id=dag_id, execution_date=execution_date)
        except AirflowStateError as state_error:
            raise ApiError(
                title='Unable to pause action',
                description=state_error.message,
                status=falcon.HTTP_409)

    def unpause_dag(self, dag_id, execution_date):
        """
        Clears the pause flag on this dag/execution
        """
        try:
            AIRFLOW_DB.unpause_dag_run(
                dag_id=dag_id, execution_date=execution_date)
        except AirflowStateError as state_error:
            raise ApiError(
                title='Unable to unpause action',
                description=state_error.message,
                status=falcon.HTTP_409)

    def stop_dag(self, dag_id, execution_date):
        """
        Sets the stop flag on this dag/execution
        """
        try:
            AIRFLOW_DB.stop_dag_run(
                dag_id=dag_id, execution_date=execution_date)
        except AirflowStateError as state_error:
            raise ApiError(
                title='Unable to stop action',
                description=state_error.message,
                status=falcon.HTTP_409)
