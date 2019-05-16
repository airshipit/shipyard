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

from shipyard_airflow.common.notes.notes import MIN_VERBOSITY
from shipyard_airflow.control.helpers.design_reference_helper import (
    DesignRefHelper
)
from shipyard_airflow.control.helpers.notes import NOTES as notes_helper
from shipyard_airflow.dags.dag_names import CRITICAL_DAG_STEPS
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


def format_action_steps(action_id, steps, verbosity=MIN_VERBOSITY):
    """ Converts a list of action step db records to desired format

    :param action_id: the action containing steps
    :param steps: the list of dictionaries of step info, in database format
    :param verbosity: the verbosity level of notes to retrieve, defaults to 1.
        if set to a value less than 1, notes will not be retrieved.
    """
    if not steps:
        return []
    steps_response = []
    step_notes_dict = notes_helper.get_all_step_notes_for_action(
        action_id=action_id,
        verbosity=verbosity
    )
    for idx, step in enumerate(steps):
        step_task_id = step.get('task_id')
        steps_response.append(
            format_step(
                action_id=action_id,
                step=step,
                index=idx + 1,
                notes=[
                    note.view()
                    for note in step_notes_dict.get(step_task_id, [])
                ]))
    return steps_response


def format_step(action_id, step, index, notes):
    """ reformat a step (dictionary) into a common response format """
    return {
        'url': '/actions/{}/steps/{}'.format(action_id, step.get('task_id')),
        'state': step.get('state'),
        'id': step.get('task_id'),
        'index': index,
        'notes': notes
    }


def get_deployment_status(action, force_completed=False):
    """Given a set of action data, make/return a set of deployment status data

    :param dict action: A dictionary of data about an action.
                        The keys of the dict should include:
                            - committed_rev_id
                            - context_marker
                            - dag_status
                            - id
                            - timestamp
                            - user
                        Any missing key will result in a piece of the
                        deployment status being "unknown"
    :param bool force_completed: optional. If True the status will be forced
                                 to "completed". This will be useful when the
                                 last step of the DAG wants to get the status
                                 of the deployment, and knows that the
                                 DAG/deployment/action really is completed even
                                 though it does not appear to be.
    :returns: A dict of deployment status data
    :rtype: dict
    """
    # Create a URL to get the documents in Deckhand, using the Deckhand
    # revision ID associated with the action
    document_url = DesignRefHelper().get_design_reference_href(
        action.get('committed_rev_id', 'unknown'))

    # Create the "status" and "result" of the deployment
    dag_status = action.get('dag_status', '').upper()
    status = 'running'
    result = 'unknown'
    status_result_map = {
        'FAILED': 'failed',
        'UPSTREAM_FAILED': 'failed',
        'SKIPPED': 'failed',
        'REMOVED': 'failed',
        'SHUTDOWN': 'failed',
        'SUCCESS': 'successful'
    }
    if dag_status in status_result_map:
        # We don't need to check anything else, we know the status of the
        # deployment is completed and we can map directly to a result
        status = 'completed'
        result = status_result_map[dag_status]
    else:
        # The DAG could still be running, or be in some other state, so we
        # need to dig into the DAG to determine what the result really is
        # Use an ActionsHelper to check all the DAG steps
        helper = ActionsHelper(action.get('id'))
        result = helper.get_result_from_dag_steps()

    # Check to see if we need to override the status to "completed"
    if force_completed:
        status = "completed"

    # Return the dictionary of data
    return {
        'status': status,
        'results': result,
        'context-marker': action.get('context_marker', 'unknown'),
        'action': action.get('id', 'unknown'),
        'document_url': document_url,
        'user': action.get('user', 'unknown'),
        'date': action.get('timestamp', 'unknown')
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

    def _get_latest_steps(self):
        """Get all the steps for the action, and return the latest try on each

        :returns: All dictionary of task_id (a string name) to step details
        :rtype: dict
        """
        latest_steps = {}
        for step in self._get_all_steps():
            task_id = step['task_id']
            if task_id in latest_steps:
                # We already have this step, see if this one is more recent
                # than the one we already have
                if step['try_number'] > latest_steps[task_id]['try_number']:
                    latest_steps[task_id] = step
            else:
                # Step we have not seen yet
                latest_steps[task_id] = step

        return latest_steps

    def get_result_from_dag_steps(self):
        """Look up the DAG steps, and create a result string based on the state
        of the DAG steps

        We will only check "critical" steps, as these are what's most
        important, and won't even run if other steps fail in the first place
        If any critical steps have a state that falls under our success states
        and no other critical steps have a state that falls under the failed or
        running states, result will be "successful"
        If any critical steps have a state that fall under our failed states,
        result will be "failed"
        If any critical steps have a state that fall under our running states,
        result will be "pending"
        If no critical steps have states that fall under any of the state sets,
        result will be "unknown"

        :returns: The result of the DAG based on the DAG's steps
        :rtype: str
        """
        result = 'unknown'
        running_states = [
            None,
            'None',
            'scheduled',
            'queued',
            'running',
            'up_for_retry',
            'up_for_reschedule'
        ]
        failed_states = ['shutdown', 'failed', 'upstream_failed']
        success_states = ['skipped', 'success']
        latest_steps = self._get_latest_steps()
        for step_id in CRITICAL_DAG_STEPS:
            if step_id in latest_steps:
                state = latest_steps[step_id]['state']
                if state in success_states and result == 'unknown':
                    result = 'successful'
                elif state in failed_states:
                    result = 'failed'
                    break
                elif state in running_states:
                    result = 'pending'
                elif state not in success_states:
                    # The state we are looking at doesn't fall under any of our
                    # known states
                    LOG.warning('Found DAG step with unexpected state: {}'.
                                format(state))
                    result = 'unknown'
                    break

        return result

    def get_step(self, step_id, try_number=None):
        """
        :param step_id: Step ID - task_id in db
        :param try_number: Number of try - try_number in db

        returns: Step
        """
        # Retrieve step. Note that we will get a list and it will
        # be the content of step[0]
        step_list = [x for x in
                     self._get_all_steps()
                     if step_id == x['task_id'] and
                     (try_number is None or try_number == x['try_number'])
                     ]
        # try_number is needed to get correct task from correct worker
        # the worker host for request URL
        # is referenced in correct task's 'hostname' field

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
