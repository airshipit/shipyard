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
import logging
import os

import falcon
import requests
from requests.exceptions import RequestException
from dateutil.parser import parse
from oslo_config import cfg
import ulid

from shipyard_airflow import policy
from shipyard_airflow.control.helpers.action_helper import (
    determine_lifecycle,
    format_action_steps
)
from shipyard_airflow.control.action import action_validators
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.control.helpers import configdocs_helper
from shipyard_airflow.control.helpers.configdocs_helper import (
    ConfigdocsHelper)
from shipyard_airflow.control.helpers.notes import NOTES as notes_helper
from shipyard_airflow.control.json_schemas import ACTION
from shipyard_airflow.db.db import AIRFLOW_DB, SHIPYARD_DB
from shipyard_airflow.errors import ApiError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def _action_mappings():
    # Return dictionary mapping actions to their dags and validators
    return {
        'deploy_site': {
            'dag': 'deploy_site',
            'rbac_policy': policy.ACTION_DEPLOY_SITE,
            'validators': [
                action_validators.validate_committed_revision,
                action_validators.validate_intermediate_commits,
                action_validators.validate_deployment_action_full,
            ]
        },
        'update_site': {
            'dag': 'update_site',
            'rbac_policy': policy.ACTION_UPDATE_SITE,
            'validators': [
                action_validators.validate_committed_revision,
                action_validators.validate_intermediate_commits,
                action_validators.validate_deployment_action_full,
            ]
        },
        'update_software': {
            'dag': 'update_software',
            'rbac_policy': policy.ACTION_UPDATE_SOFTWARE,
            'validators': [
                action_validators.validate_committed_revision,
                action_validators.validate_intermediate_commits,
                action_validators.validate_deployment_action_basic,
            ]
        },
        'redeploy_server': {
            'dag': 'redeploy_server',
            'rbac_policy': policy.ACTION_REDEPLOY_SERVER,
            'validators': [
                action_validators.validate_target_nodes,
                action_validators.validate_committed_revision,
                action_validators.validate_deployment_action_basic,
            ]
        },
        'relabel_nodes': {
            'dag': 'relabel_nodes',
            'rbac_policy': policy.ACTION_RELABEL_NODES,
            'validators': [
                action_validators.validate_target_nodes,
                action_validators.validate_committed_revision,
                action_validators.validate_deployment_action_basic,
            ]
        },
        'test_site': {
            'dag': 'test_site',
            'rbac_policy': policy.ACTION_TEST_SITE,
            'validators': []
        }
    }


# /api/v1.0/actions
class ActionsResource(BaseResource):
    """
    The actions resource represent the asyncrhonous invocations of shipyard
    """

    @policy.ApiEnforcer(policy.LIST_ACTIONS)
    def on_get(self, req, resp, **kwargs):
        """
        Return actions that have been invoked through shipyard.
        :returns: a json array of action entities
        """
        resp.text = self.to_json(self.get_all_actions(
            verbosity=req.context.verbosity)
        )
        resp.status = falcon.HTTP_200

    @policy.ApiEnforcer(policy.CREATE_ACTION)
    def on_post(self, req, resp, **kwargs):
        """
        Accept an action into shipyard
        """
        # The 'allow-intermediate-commits' query parameter is set to False
        # unless explicitly set to True
        allow_intermediate_commits = (
            req.get_param_as_bool(name='allow-intermediate-commits'))

        input_action = self.req_json(req, validate_json_schema=ACTION)
        action = self.create_action(
            action=input_action,
            context=req.context,
            allow_intermediate_commits=allow_intermediate_commits)

        LOG.info("Id %s generated for action %s", action['id'], action['name'])
        # respond with the action and location for checking status
        resp.status = falcon.HTTP_201
        resp.text = self.to_json(action)
        resp.location = '/api/v1.0/actions/{}'.format(action['id'])

    def create_action(self, action, context, allow_intermediate_commits=False):
        # use uuid assigned for this request as the id of the action.
        action['id'] = ulid.ulid()
        # the invoking user
        action['user'] = context.user
        # add current timestamp (UTC) to the action.
        action['timestamp'] = str(datetime.utcnow())
        # add external marker that is the passed with request context
        action['context_marker'] = context.request_id
        # validate that action is supported.
        LOG.info("Attempting action: %s", action['name'])
        action_mappings = _action_mappings()
        if action['name'] not in action_mappings:
            raise ApiError(
                title='Unable to start action',
                description='Unsupported Action: {}'.format(action['name']))

        action_cfg = action_mappings.get(action['name'])

        # check access to specific actions - lack of access will exception out
        policy.check_auth(context, action_cfg['rbac_policy'])

        dag = action_cfg['dag']
        action['dag_id'] = dag

        # Set up configdocs_helper
        self.configdocs_helper = ConfigdocsHelper(context)

        # Retrieve last committed design revision
        action['committed_rev_id'] = self.get_committed_design_version()
        # Set if intermediate commits are ignored
        action['allow_intermediate_commits'] = allow_intermediate_commits

        # populate action parameters if they are not set
        if 'parameters' not in action:
            action['parameters'] = {}

        for validator in action_cfg['validators']:
            # validators will raise ApiError if they fail validation.
            # validators are expected to accept action as a parameter, but
            # handle all other kwargs (e.g. def vdtr(action, **kwargs): even if
            # they don't use that parameter.
            validator(action=action, configdocs_helper=self.configdocs_helper)

        # invoke airflow, get the dag's date
        dag_execution_date = self.invoke_airflow_dag(
            dag_id=dag, action=action, context=context)
        # set values on the action
        action['dag_execution_date'] = dag_execution_date
        action['dag_status'] = 'SCHEDULED'

        # insert the action into the shipyard db
        # TODO(b-str): When invoke_airflow_dag triggers a DAG but fails to
        #    respond properly, no record is inserted, so there is a running
        #    process with no tracking in the Shipyard database. This is not
        #    ideal.
        self.insert_action(action=action)
        notes_helper.make_action_note(
            action_id=action['id'],
            note_val="Configdoc revision {}".format(action['committed_rev_id'])
        )
        self.audit_control_command_db({
            'id': ulid.ulid(),
            'action_id': action['id'],
            'command': 'invoke',
            'user': context.user
        })

        return action

    def get_all_actions(self, verbosity):
        """Retrieve all actions known to Shipyard

        :param verbosity: Integer 0-5, the level of verbosity applied to the
            response's notes.

        Interacts with airflow and the shipyard database to return the list of
        actions invoked through shipyard.
        """
        # fetch actions from the shipyard db
        all_actions = self.get_action_map()
        # fetch the associated dags, steps from the airflow db
        all_dag_runs = self.get_dag_run_map()
        all_tasks = self.get_all_tasks_db()

        notes = notes_helper.get_all_action_notes(verbosity=verbosity)
        # correlate the actions and dags into a list of action entites
        actions = []

        for action_id, action in all_actions.items():
            dag_key = action['dag_id'] + action['dag_execution_date']
            dag_key_id = action['dag_id']
            dag_key_date = action['dag_execution_date']
            # locate the dag run associated
            dag_state = all_dag_runs.get(dag_key, {}).get('state', None)
            # get the dag status from the dag run state
            action['dag_status'] = dag_state
            action['action_lifecycle'] = determine_lifecycle(dag_state)
            # get the steps summary
            action_tasks = [
                step for step in all_tasks
                if step['dag_id'].startswith(dag_key_id) and
                step['execution_date'].strftime(
                    '%Y-%m-%dT%H:%M:%S') == dag_key_date
            ]
            action['steps'] = format_action_steps(
                action_id=action_id,
                steps=action_tasks,
                verbosity=0
            )
            action['notes'] = []
            for note in notes.get(action_id, []):
                action['notes'].append(note.view())
            actions.append(action)

        return actions

    def get_action_map(self):
        """
        maps an array of dictionaries to a dictonary of the same results by id
        :returns: a dictionary of dictionaries keyed by action id
        """
        return {action['id']: action for action in self.get_all_actions_db()}

    def get_all_actions_db(self):
        """
        Wrapper for call to the shipyard database to get all actions
        :returns: a list of dictionaries keyed by action id
        """
        return SHIPYARD_DB.get_all_submitted_actions()

    def get_dag_run_map(self):
        """
        Maps an array of dag runs to a keyed dictionary
        :returns: a dictionary of dictionaries keyed by dag_id and
                  execution_date
        """
        return {
            run['dag_id'] +
            run['execution_date'].strftime('%Y-%m-%dT%H:%M:%S'): run
            for run in self.get_all_dag_runs_db()
        }

    def get_all_dag_runs_db(self):
        """
        Wrapper for call to the airflow db to get all dag runs
        :returns: a list of dictionaries representing dag runs in airflow
        """
        return AIRFLOW_DB.get_all_dag_runs()

    def get_all_tasks_db(self):
        """
        Wrapper for call to the airflow db to get all tasks
        :returns: a list of task dictionaries
        """
        return AIRFLOW_DB.get_all_tasks()

    def insert_action(self, action):
        """
        Wrapper for call to the shipyard db to insert an action
        """
        return SHIPYARD_DB.insert_action(action)

    def audit_control_command_db(self, action_audit):
        """
        Wrapper for the shipyard db call to record an audit of the
        action control taken
        """
        return SHIPYARD_DB.insert_action_command_audit(action_audit)

    def invoke_airflow_dag(self, dag_id, action, context):
        """
        Call airflow, and invoke a dag
        :param dag_id: the name of the dag to invoke
        :param action: the action structure to invoke the dag with
        """
        # TODO(bryan-strassner) refactor the mechanics of this method to an
        #     airflow api client module

        # Retrieve URL
        web_server_url = CONF.base.web_server
        api_path = 'api/experimental/dags/{}/dag_runs'
        req_url = os.path.join(web_server_url, api_path.format(dag_id))
        c_timeout = CONF.base.airflow_api_connect_timeout
        r_timeout = CONF.base.airflow_api_read_timeout

        if 'Error' in web_server_url:
            raise ApiError(
                title='Unable to invoke workflow',
                description=('Airflow URL not found by Shipyard. '
                             'Shipyard configuration is missing web_server '
                             'value'),
                status=falcon.HTTP_503,
                retry=True, )
        else:
            # No cache please
            headers = {'Cache-Control': 'no-cache'}
            # "conf" - JSON string that gets pickled into the DagRun's
            # conf attribute. The conf is passed as as a string of escaped
            # json inside the json payload accepted by the API.
            conf_value = self.to_json({'action': action})
            payload = {'run_id': action['id'], 'conf': conf_value}
            try:
                resp = requests.post(req_url, timeout=(c_timeout, r_timeout),
                                     headers=headers, json=payload)
                LOG.info('Response code from Airflow trigger_dag: %s',
                         resp.status_code)
                # any 4xx/5xx will be HTTPError, which are RequestException
                resp.raise_for_status()
                response = resp.json()
                LOG.info('Response from Airflow trigger_dag: %s', response)
            except RequestException as rex:
                LOG.error("Request to airflow failed: %s", rex.args)
                raise ApiError(
                    title='Unable to complete request to Airflow',
                    description=(
                        'Airflow could not be contacted properly by Shipyard.'
                    ),
                    status=falcon.HTTP_503,
                    error_list=[{
                        'message': str(type(rex))
                    }],
                    retry=True, )

            dag_time = self._exhume_date(dag_id,
                                         response['message'])
            dag_execution_date = dag_time.strftime('%Y-%m-%dT%H:%M:%S')
            return dag_execution_date

    def _exhume_date(self, dag_id, log_string):
        # we are unable to use the response time because that
        # does not match the time when the dag was recorded.
        # We have to parse the returned message to find the
        # Created <DagRun {dag_id} @ {timestamp}
        # e.g.
        # ...- Created <DagRun deploy_site @ 2017-09-22 22:16:14: man...
        # split on "Created <DagRun deploy_site @ ", then ': "
        # should get to the desired date string.
        #
        # returns the date found in a date object
        log_split = log_string.split('Created <DagRun {} @ '.format(dag_id))
        if len(log_split) < 2:
            raise ApiError(
                title='Unable to determine if workflow has started',
                description=(
                    'Airflow has not responded with parseable output. '
                    'Shipyard is unable to determine run timestamp'),
                status=falcon.HTTP_500,
                error_list=[{
                    'message': log_string
                }],
                retry=True
            )
        else:
            # everything before the ': ' should be a date/time
            date_split = log_split[1].split(': ')[0]
            try:
                return parse(date_split, ignoretz=True)
            except ValueError as valerr:
                raise ApiError(
                    title='Unable to determine if workflow has started',
                    description=('Airflow has not responded with parseable '
                                 'output. Shipyard is unable to determine run '
                                 'timestamp'),
                    status=falcon.HTTP_500,
                    error_list=[{
                        'message': 'value {} has caused {}'.format(date_split,
                                                                   valerr)
                    }],
                    retry=True,
                )

    def get_committed_design_version(self):
        """Retrieves the committed design version from Deckhand.

        Returns None if there is no committed version
        """
        committed_rev_id = self.configdocs_helper.get_revision_id(
            configdocs_helper.COMMITTED
        )
        if committed_rev_id:
            LOG.info("The committed revision in Deckhand is %d",
                     committed_rev_id)
            return committed_rev_id
        LOG.info("No committed revision found in Deckhand")
        return None
