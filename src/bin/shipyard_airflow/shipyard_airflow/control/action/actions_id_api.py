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
from shipyard_airflow.control.action.action_helper import (determine_lifecycle,
                                                           format_action_steps)
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.db.db import AIRFLOW_DB, SHIPYARD_DB
from shipyard_airflow.errors import ApiError


# /api/v1.0/actions/{action_id}
class ActionsIdResource(BaseResource):
    """
    The actions resource represent the asyncrhonous invocations of shipyard
    """
    @policy.ApiEnforcer('workflow_orchestrator:get_action')
    def on_get(self, req, resp, **kwargs):
        """
        Return actions that have been invoked through shipyard.
        :returns: a json array of action entities
        """
        resp.body = self.to_json(self.get_action(kwargs['action_id']))
        resp.status = falcon.HTTP_200

    def get_action(self, action_id):
        """
        Interacts with airflow and the shipyard database to return the
        requested action invoked through shipyard.
        """
        # get the action from shipyard db
        action = self.get_action_db(action_id=action_id)
        if action is None:
            raise ApiError(
                title='Action not found',
                description='Unknown Action: {}'.format(action_id),
                status=falcon.HTTP_404)

        # lookup the dag and tasks based on the associated dag_id,
        # execution_date
        dag_id = action['dag_id']
        dag_execution_date = action['dag_execution_date']

        dag = self.get_dag_run_by_id(dag_id, dag_execution_date)
        steps = self.get_tasks_db(dag_id, dag_execution_date)
        if dag is not None:
            # put the values together into an "action" object
            action['dag_status'] = dag['state']
            action['action_lifecycle'] = determine_lifecycle(dag['state'])
            action['steps'] = format_action_steps(action_id, steps)
        action['validations'] = self.get_validations_db(action_id)
        action['command_audit'] = self.get_action_command_audit_db(action_id)
        return action

    def get_dag_run_by_id(self, dag_id, execution_date):
        """
        Wrapper for call to the airflow db to get a dag_run
        :returns: a dag run dictionary
        """
        dag_run_list = self.get_dag_run_db(dag_id, execution_date)
        # should be only one result, return the first one
        if dag_run_list:
            return dag_run_list[0]
        else:
            return None

    def get_action_db(self, action_id):
        """
        Wrapper for call to the shipyard database to get an action
        :returns: a dictionary of action details.
        """
        return SHIPYARD_DB.get_action_by_id(
            action_id=action_id)

    def get_validations_db(self, action_id):
        """
        Wrapper for call to the shipyard db to get validations associated with
        an action
        :returns: an array of dictionaries of validation details.
        """
        return SHIPYARD_DB.get_validation_by_action_id(
            action_id=action_id)

    def get_tasks_db(self, dag_id, execution_date):
        """
        Wrapper for call to the airflow db to get all tasks
        :returns: a list of task dictionaries
        """
        return AIRFLOW_DB.get_tasks_by_id(
            dag_id=dag_id, execution_date=execution_date)

    def get_dag_run_db(self, dag_id, execution_date):
        """
        Wrapper for call to the airflow db to get a dag_run
        :returns: a dag run dictionaries
        """
        return AIRFLOW_DB.get_dag_runs_by_id(
            dag_id=dag_id, execution_date=execution_date)

    def get_action_command_audit_db(self, action_id):
        """
        Wrapper for call to the shipyard db to get the history of
        action command audit records
        """
        return SHIPYARD_DB.get_command_audit_by_action_id(action_id)
