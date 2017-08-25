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
from shipyard_airflow.db.db import AIRFLOW_DB, SHIPYARD_DB
from shipyard_airflow.errors import ApiError


# /api/v1.0/actions/{action_id}/steps/{step_id}
class ActionsStepsResource(BaseResource):
    """
    The actions steps resource is the steps of an action
    """
    @policy.ApiEnforcer('workflow_orchestrator:get_action_step')
    def on_get(self, req, resp, **kwargs):
        """
        Return step details for an action step
        :returns: a json object describing a step
        """
        resp.body = self.to_json(
            self.get_action_step(kwargs['action_id'], kwargs['step_id']))
        resp.status = falcon.HTTP_200

    def get_action_step(self, action_id, step_id):
        """
        Interacts with airflow and the shipyard database to return the
        requested step invoked through shipyard.
        """
        action = self.get_action_db(action_id=action_id)

        if action is None:
            raise ApiError(
                title='Action not found',
                description='Unknown action {}'.format(action_id),
                status=falcon.HTTP_404)

        # resolve the ids for lookup of steps
        dag_id = action['dag_id']
        dag_execution_date = action['dag_execution_date']

        # get the action steps from shipyard db
        steps = self.get_tasks_db(dag_id, dag_execution_date)

        for idx, step in enumerate(steps):
            if step_id == step['task_id']:
                # TODO (Bryan Strassner) more info about the step?
                #                        like logs? Need requirements defined
                step['index'] = idx + 1
                return step

        # if we didn't find it, 404
        raise ApiError(
            title='Step not found',
            description='Unknown step {}'.format(step_id),
            status=falcon.HTTP_404)

    def get_action_db(self, action_id):
        """
        Wrapper for call to the shipyard database to get an action
        :returns: a dictionary of action details.
        """
        return SHIPYARD_DB.get_action_by_id(
            action_id=action_id)

    def get_tasks_db(self, dag_id, execution_date):
        """
        Wrapper for call to the airflow db to get all tasks for a dag run
        :returns: a list of task dictionaries
        """
        return AIRFLOW_DB.get_tasks_by_id(
            dag_id=dag_id, execution_date=execution_date)
