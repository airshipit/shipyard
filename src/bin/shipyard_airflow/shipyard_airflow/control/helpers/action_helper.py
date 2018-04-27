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
""" Common methods for use by action api classes as necessary """
from datetime import datetime
import falcon
import logging

from shipyard_airflow.db.db import AIRFLOW_DB, SHIPYARD_DB
from shipyard_airflow.errors import ApiError


LOG = logging.getLogger(__name__)


DAG_STATE_MAPPING = {
    'QUEUED': 'Pending',
    'RUNNING': 'Processing',
    'SUCCESS': 'Complete',
    'SHUTDOWN': 'Failed',
    'FAILED': 'Failed',
    'UP_FOR_RETRY': 'Processing',
    'UPSTREAM_FAILED': 'Failed',
    'SKIPPED': 'Failed',
    'REMOVED': 'Failed',
    'SCHEDULED': 'Pending',
    'NONE': 'Pending',
    'PAUSED': 'Paused'
}


def determine_lifecycle(dag_status=None):
    """ Convert a dag_status to an action_lifecycle value """
    if dag_status is None:
        dag_status = 'NONE'
    lifecycle = DAG_STATE_MAPPING.get(dag_status.upper())
    if lifecycle is None:
        lifecycle = 'Unknown ({})'.format(dag_status)
    return lifecycle


def format_action_steps(action_id, steps):
    """ Converts a list of action step db records to desired format """
    if not steps:
        return []
    steps_response = []
    for idx, step in enumerate(steps):
        steps_response.append(format_step(action_id=action_id,
                                          step=step,
                                          index=idx + 1))
    return steps_response


def format_step(action_id, step, index):
    """ reformat a step (dictionary) into a common response format """
    return {
        'url': '/actions/{}/steps/{}'.format(action_id, step.get('task_id')),
        'state': step.get('state'),
        'id': step.get('task_id'),
        'index': index
    }


class ActionsHelper(object):
    """
    A helper class for Shipyard actions
    """
    def __init__(self, action_id):
        """Initialization of ActionsHelper object.
        :param action_id: Shipyard action ID

        """
        self.action_id = action_id
        self.action = self._get_action_info()

        LOG.debug("Initialized ActionHelper for action_id: %s", self.action_id)

    def _get_action_info(self):
        """
        :returns: Action Information
        """
        # Retrieve information related to the action id
        action = self._get_action_db(self.action_id)

        if not action:
            raise ApiError(
                title='Action Not Found!',
                description='Unknown Action {}'.format(self.action_id),
                status=falcon.HTTP_404)
        else:
            return action

    def _get_dag_info(self):
        """
        returns: Dag Information
        """
        # Retrieve 'dag_id' and 'dag_execution_date'
        dag_id = self.action.get('dag_id')
        dag_execution_date = self.action.get('dag_execution_date')

        if not dag_id:
            raise ApiError(
                title='Dag ID Not Found!',
                description='Unable to retrieve Dag ID',
                status=falcon.HTTP_404)
        elif not dag_execution_date:
            raise ApiError(
                title='Execution Date Not Found!',
                description='Unable to retrieve Execution Date',
                status=falcon.HTTP_404)
        else:
            return dag_id, dag_execution_date

    def _get_all_steps(self):
        """
        returns: All steps for the action ID
        """
        # Retrieve dag_id and dag_execution_date
        dag_id, dag_execution_date = self._get_dag_info()

        # Retrieve the action steps
        steps = self._get_tasks_db(dag_id, dag_execution_date)

        if not steps:
            raise ApiError(
                title='Steps Not Found!',
                description='Unable to retrieve Information on Steps',
                status=falcon.HTTP_404)
        else:
            LOG.debug("%s steps found for action %s",
                      len(steps), self.action_id)
            LOG.debug("The steps for action %s are as follows:",
                      self.action_id)
            LOG.debug(steps)

            return steps

    def get_step(self, step_id):
        """
        returns: Step
        """
        # Retrieve step. Note that we will get a list and it will
        # be the content of step[0]
        step_list = [x for x in
                     self._get_all_steps()
                     if step_id == x['task_id']]

        if not step_list:
            raise ApiError(
                title='Step Not Found!',
                description='Unable to retrieve Step',
                status=falcon.HTTP_404)
        else:
            step = step_list[0]
            LOG.debug("Step Located:")
            LOG.debug(step)

            return step

    @staticmethod
    def get_formatted_dag_execution_date(step):
        """
        :returns: dag_execution_date
        """
        strftime = datetime.strftime
        return step['execution_date'].strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def parse_action_id(**kwargs):
        """
        Retreive action_id from the input parameters
        Action_id must be a 26 character ulid.
        """
        action_id = kwargs.get('action_id')
        if action_id is None or not len(action_id) == 26:
            raise ApiError(
                title='Invalid Action ID!',
                description='An invalid action ID was specified',
                status=falcon.HTTP_400)

        LOG.debug("Action ID parsed: %s", action_id)

        return action_id

    @staticmethod
    def parse_step_id(**kwargs):
        """
        Retreive step_id from the input parameters
        """
        step_id = kwargs.get('step_id')
        if step_id is None:
            raise ApiError(
                title='Missing Step ID!',
                description='Missing Step ID',
                status=falcon.HTTP_400)

        LOG.debug("Step ID parsed: %s", step_id)

        return step_id

    @staticmethod
    def _get_action_db(action_id):
        """
        Wrapper for call to the shipyard database to get an action
        :returns: a dictionary of action details.
        """
        return SHIPYARD_DB.get_action_by_id(
            action_id=action_id)

    @staticmethod
    def _get_tasks_db(dag_id, execution_date):
        """
        Wrapper for call to the airflow db to get all tasks for a dag run
        :returns: a list of task dictionaries
        """
        return AIRFLOW_DB.get_tasks_by_id(
            dag_id=dag_id, execution_date=execution_date)
