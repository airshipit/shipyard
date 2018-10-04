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
import json
import logging
import os
from unittest import mock
from unittest.mock import patch

import falcon
from falcon import testing
from oslo_config import cfg
import pytest
import responses

from shipyard_airflow.common.notes.notes import NotesManager
from shipyard_airflow.common.notes.notes_helper import NotesHelper
from shipyard_airflow.common.notes.storage_impl_mem import (
    MemoryNotesStorage
)
from shipyard_airflow.control.action import actions_api
from shipyard_airflow.control.action.actions_api import ActionsResource
from shipyard_airflow.control.base import ShipyardRequestContext
from shipyard_airflow.control.helpers.configdocs_helper import (
    ConfigdocsHelper
)
from shipyard_airflow.errors import ApiError
from shipyard_airflow.policy import ShipyardPolicy

DATE_ONE = datetime(2017, 9, 13, 11, 13, 3, 57000)
DATE_TWO = datetime(2017, 9, 13, 11, 13, 5, 57000)
DATE_ONE_STR = DATE_ONE.strftime('%Y-%m-%dT%H:%M:%S')
DATE_TWO_STR = DATE_TWO.strftime('%Y-%m-%dT%H:%M:%S')
DESIGN_VERSION = 1

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_token():
    """Stub method to use for NotesHelper/NotesManager"""
    return "token"

# Notes helper that can be mocked into various objects to prevent database
# dependencies
nh = NotesHelper(NotesManager(MemoryNotesStorage(), get_token))


def create_req(ctx, body):
    '''creates a falcon request'''
    env = testing.create_environ(
        path='/',
        query_string='',
        protocol='HTTP/1.1',
        scheme='http',
        host='falconframework.org',
        port=None,
        headers={'Content-Type': 'application/json'},
        app='',
        body=body,
        method='POST',
        wsgierrors=None,
        file_wrapper=None)
    req = falcon.Request(env)
    req.context = ctx
    return req


def create_resp():
    '''creates a falcon response'''
    resp = falcon.Response()
    return resp


def actions_db():
    """
    replaces the actual db call
    """
    return [
        {
            'id': 'aaaaaa',
            'name': 'dag_it',
            'parameters': None,
            'dag_id': 'did1',
            'dag_execution_date': DATE_ONE_STR,
            'user': 'robot1',
            'timestamp': DATE_ONE,
            'context_marker': '8-4-4-4-12a'
        },
        {
            'id': 'bbbbbb',
            'name': 'dag2',
            'parameters': {
                'p1': 'p1val'
            },
            'dag_id': 'did2',
            'dag_execution_date': DATE_ONE_STR,
            'user': 'robot2',
            'timestamp': DATE_ONE,
            'context_marker': '8-4-4-4-12b'
        },
    ]


def dag_runs_db():
    """
    replaces the actual db call
    """
    return [
        {
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO
        },
        {
            'dag_id': 'did1',
            'execution_date': DATE_ONE,
            'state': 'FAILED',
            'run_id': '99',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_ONE
        },
    ]


def tasks_db():
    """
    replaces the actual db call
    """
    return [
        {
            'task_id': '1a',
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO,
            'duration': '20mins',
            'try_number': '1',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
        {
            'task_id': '1b',
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO,
            'duration': '1minute',
            'try_number': '1',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
        {
            'task_id': '1c',
            'dag_id': 'did2',
            'execution_date': DATE_ONE,
            'state': 'SUCCESS',
            'run_id': '12345',
            'external_trigger': 'something',
            'start_date': DATE_ONE,
            'end_date': DATE_TWO,
            'duration': '1day',
            'try_number': '3',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
        {
            'task_id': '2a',
            'dag_id': 'did1',
            'execution_date': DATE_ONE,
            'state': 'FAILED',
            'start_date': DATE_ONE,
            'end_date': DATE_ONE,
            'duration': '1second',
            'try_number': '2',
            'operator': 'smooth',
            'queued_dttm': DATE_TWO
        },
    ]


def airflow_stub(**kwargs):
    """
    asserts that the airflow invocation method was called with the right
    parameters
    """
    assert kwargs['dag_id']
    assert kwargs['action']
    return '2017-09-06 14:10:08.528402'


def insert_action_stub(**kwargs):
    """
    asserts that the insert action was called with the right parameters
    """
    assert kwargs['action']


def audit_control_command_db(action_audit):
    """
    Stub for inserting the invoke record
    """
    assert action_audit['command'] == 'invoke'


@pytest.fixture(scope='function')
def conf_fixture(request):
    def set_override(name, override, group):
        CONF = cfg.CONF
        CONF.set_override(name, override, group=group)
        request.addfinalizer(CONF.clear_override(name, group=group))

    return set_override


context = ShipyardRequestContext()


@mock.patch.object(ShipyardPolicy, 'authorize', return_value=True)
@mock.patch.object(
    ActionsResource,
    'get_all_actions',
    return_value={'id': 'test_id',
                  'name': 'test_name'})
def test_on_get(mock_get_all_actions, mock_authorize):
    act_resource = ActionsResource()
    context.policy_engine = ShipyardPolicy()
    req = create_req(context, None)
    resp = create_resp()
    act_resource.on_get(req, resp)
    mock_authorize.assert_called_once_with(
        'workflow_orchestrator:list_actions', context)
    assert mock_get_all_actions.call_count == 1
    assert resp.body is not None
    assert resp.status == '200 OK'


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch.object(ShipyardPolicy, 'authorize', return_value=True)
@mock.patch.object(
    ActionsResource,
    'create_action',
    return_value={'id': 'test_id',
                  'name': 'test_name'})
@patch('logging.Logger.info')
def test_on_post(mock_info, mock_create_action, mock_authorize, *args):
    act_resource = ActionsResource()
    context.policy_engine = ShipyardPolicy()
    json_body = json.dumps({
        'user': "test_user",
        'req_id': "test_req_id",
        'external_ctx': "test_ext_ctx",
        'name': "test_name"
    }).encode('utf-8')
    req = create_req(context, json_body)
    resp = create_resp()
    act_resource.on_post(req, resp)
    mock_authorize.assert_called_once_with(
        'workflow_orchestrator:create_action', context)
    mock_create_action.assert_called_once_with(
        action=json.loads(json_body.decode('utf-8')),
        context=context,
        allow_intermediate_commits=None)
    mock_info.assert_called_with("Id %s generated for action %s", 'test_id',
                                 'test_name')
    assert resp.status == '201 Created'
    assert resp.body is not None
    assert '/api/v1.0/actions/' in resp.location


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
def test_get_all_actions(*args):
    """
    Tests the main response from get all actions
    """
    action_resource = ActionsResource()
    action_resource.get_all_actions_db = actions_db
    action_resource.get_all_dag_runs_db = dag_runs_db
    action_resource.get_all_tasks_db = tasks_db
    result = action_resource.get_all_actions(verbosity=1)
    assert len(result) == len(actions_db())
    for action in result:
        if action['name'] == 'dag_it':
            assert len(action['steps']) == 1
            assert action['dag_status'] == 'FAILED'
        if action['name'] == 'dag2':
            assert len(action['steps']) == 3
            assert action['dag_status'] == 'SUCCESS'


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
def test_get_all_actions_notes(*args):
    """
    Tests the main response from get all actions
    """
    action_resource = ActionsResource()
    action_resource.get_all_actions_db = actions_db
    action_resource.get_all_dag_runs_db = dag_runs_db
    action_resource.get_all_tasks_db = tasks_db
    # inject some notes
    nh.make_action_note('aaaaaa', "hello from aaaaaa1")
    nh.make_action_note('aaaaaa', "hello from aaaaaa2")
    nh.make_action_note('bbbbbb', "hello from bbbbbb")

    result = action_resource.get_all_actions(verbosity=1)
    assert len(result) == len(actions_db())
    for action in result:
        if action['id'] == 'aaaaaa':
            assert len(action['notes']) == 2
        if action['id'] == 'bbbbbb':
            assert len(action['notes']) == 1
            assert action['notes'][0]['note_val'] == 'hello from bbbbbb'


def _gen_action_resource_stubbed():
    # TODO(bryan-strassner): mabye subclass this instead?
    action_resource = ActionsResource()
    action_resource.get_all_actions_db = actions_db
    action_resource.get_all_dag_runs_db = dag_runs_db
    action_resource.get_all_tasks_db = tasks_db
    action_resource.invoke_airflow_dag = airflow_stub
    action_resource.insert_action = insert_action_stub
    action_resource.audit_control_command_db = audit_control_command_db
    action_resource.get_committed_design_version = lambda: DESIGN_VERSION
    return action_resource


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_full')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_intermediate_commits')
def test_create_action_invalid_input(ic_val, full_val, basic_val, *args):
    action_resource = _gen_action_resource_stubbed()
    # with invalid input. fail.
    with pytest.raises(ApiError):
        action = action_resource.create_action(
            action={'name': 'broken',
                    'parameters': {
                        'a': 'aaa'
                    }},
            context=context,
            allow_intermediate_commits=False)
    assert not ic_val.called
    assert not full_val.called
    assert not basic_val.called


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.policy.check_auth')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_full')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_intermediate_commits')
def test_create_action_valid_input_and_params(ic_val, full_val, *args):
    action_resource = _gen_action_resource_stubbed()
    # with valid input and some parameters
    try:
        action = action_resource.create_action(
            action={'name': 'deploy_site',
                    'parameters': {
                        'a': 'aaa'
                    }},
            context=context,
            allow_intermediate_commits=False)
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
        assert action['committed_rev_id'] == 1
    except ApiError:
        assert False, 'Should not raise an ApiError'
    full_val.assert_called_once_with(
        action=action, configdocs_helper=action_resource.configdocs_helper)
    ic_val.assert_called_once_with(
        action=action, configdocs_helper=action_resource.configdocs_helper)


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.policy.check_auth')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_full')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_intermediate_commits')
def test_create_action_valid_input_no_params(ic_val, full_val, *args):
    action_resource = _gen_action_resource_stubbed()
    # with valid input and no parameters
    try:
        action = action_resource.create_action(
            action={'name': 'deploy_site'},
            context=context,
            allow_intermediate_commits=False)
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
        assert action['committed_rev_id'] == 1
    except ApiError:
        assert False, 'Should not raise an ApiError'
    full_val.assert_called_once_with(
        action=action, configdocs_helper=action_resource.configdocs_helper)
    ic_val.assert_called_once_with(
        action=action, configdocs_helper=action_resource.configdocs_helper)


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.policy.check_auth')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_full',
            side_effect=ApiError(title='bad'))
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_intermediate_commits')
def test_create_action_validator_error(*args):
    action_resource = _gen_action_resource_stubbed()
    # with valid input and some parameters
    with pytest.raises(ApiError) as apie:
        action = action_resource.create_action(
            action={'name': 'deploy_site',
                    'parameters': {
                        'a': 'aaa'
                    }},
            context=context,
            allow_intermediate_commits=False)
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
        assert action['committed_rev_id'] == 1

    assert apie.value.title == 'bad'


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.policy.check_auth')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
def test_create_targeted_action_valid_input_and_params(basic_val, *args):
    action_resource = _gen_action_resource_stubbed()
    # with valid input and some parameters
    try:
        action = action_resource.create_action(
            action={'name': 'redeploy_server',
                    'parameters': {
                        'target_nodes': ['node1']
                    }},
            context=context,
            allow_intermediate_commits=False)
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
        assert action['committed_rev_id'] == 1
    except ApiError:
        assert False, 'Should not raise an ApiError'
    basic_val.assert_called_once_with(
        action=action, configdocs_helper=action_resource.configdocs_helper)


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.policy.check_auth')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
def test_create_targeted_action_valid_input_missing_target(basic_val, *args):
    action_resource = _gen_action_resource_stubbed()
    # with valid input and some parameters
    with pytest.raises(ApiError) as apie:
        action = action_resource.create_action(
            action={'name': 'redeploy_server',
                    'parameters': {
                        'target_nodes': []
                    }},
            context=context,
            allow_intermediate_commits=False)
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
        assert action['committed_rev_id'] == 1
    assert apie.value.title == 'Invalid target_nodes parameter'
    assert not basic_val.called


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.policy.check_auth')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
def test_create_targeted_action_valid_input_missing_param(basic_val, *args):
    action_resource = _gen_action_resource_stubbed()
    # with valid input and some parameters
    with pytest.raises(ApiError) as apie:
        action = action_resource.create_action(
            action={'name': 'redeploy_server'},
            context=context,
            allow_intermediate_commits=False)
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
        assert action['committed_rev_id'] == 1
    assert apie.value.title == 'Invalid target_nodes parameter'
    assert not basic_val.called


@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.policy.check_auth')
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic')
def test_create_targeted_action_no_committed(basic_val, *args):
    action_resource = _gen_action_resource_stubbed()
    action_resource.get_committed_design_version = lambda: None
    # with valid input and some parameters
    with pytest.raises(ApiError) as apie:
        action = action_resource.create_action(
            action={'name': 'redeploy_server',
                    'parameters': {
                        'target_nodes': ['node1']
                    }},
            context=context,
            allow_intermediate_commits=False)
        assert action['timestamp']
        assert action['id']
        assert len(action['id']) == 26
        assert action['dag_execution_date'] == '2017-09-06 14:10:08.528402'
        assert action['dag_status'] == 'SCHEDULED'
        assert action['committed_rev_id'] == 1
    assert apie.value.title == 'No committed configdocs'
    assert not basic_val.called


# Purposefully raising Exception to test only the value passed to auth
@mock.patch('shipyard_airflow.control.action.actions_api.notes_helper',
            new=nh)
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_basic',
            side_effect=Exception('purposeful'))
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_deployment_action_full',
            side_effect=Exception('purposeful'))
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_intermediate_commits',
            side_effect=Exception('purposeful'))
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_target_nodes',
            side_effect=Exception('purposeful'))
@mock.patch('shipyard_airflow.control.action.action_validators'
            '.validate_test_cleanup',
            side_effect=Exception('purposeful'))
@mock.patch('shipyard_airflow.policy.check_auth')
def test_auth_alignment(auth, *args):
    action_resource = _gen_action_resource_stubbed()
    for action_name, action_cfg in actions_api._action_mappings().items():
        with pytest.raises(Exception) as ex:
            action = action_resource.create_action(
                action={'name': action_name},
                context=context,
                allow_intermediate_commits=False)
        assert 'purposeful' in str(ex)
        assert auth.called_with(action_cfg['rbac_policy'])
        assert (action_cfg['rbac_policy'] ==
                'workflow_orchestrator:action_{}'.format(action_name))


@patch('shipyard_airflow.db.shipyard_db.ShipyardDbAccess.'
       'get_all_submitted_actions')
def test_get_all_actions_db(mock_get_all_submitted_actions):
    act_resource = ActionsResource()
    act_resource.get_all_actions_db()
    assert mock_get_all_submitted_actions.called


@patch('shipyard_airflow.db.airflow_db.AirflowDbAccess.get_all_dag_runs')
def test_get_all_dag_runs_db(mock_get_all_dag_runs):
    act_resource = ActionsResource()
    act_resource.get_all_dag_runs_db()
    assert mock_get_all_dag_runs.called


@patch('shipyard_airflow.db.airflow_db.AirflowDbAccess.get_all_tasks')
def test_get_all_tasks_db(mock_get_all_tasks):
    act_resource = ActionsResource()
    act_resource.get_all_tasks_db()
    assert mock_get_all_tasks.called


@patch('shipyard_airflow.db.shipyard_db.ShipyardDbAccess.insert_action')
def test_insert_action(mock_insert_action):
    act_resource = ActionsResource()
    action = 'test_action'
    act_resource.insert_action(action)
    mock_insert_action.assert_called_with(action)


@patch('shipyard_airflow.db.shipyard_db.ShipyardDbAccess.'
       'insert_action_command_audit')
def test_audit_control_command_db(mock_insert_action_audit):
    act_resource = ActionsResource()
    action_audit = 'test_action_audit'
    act_resource.audit_control_command_db(action_audit)
    mock_insert_action_audit.assert_called_with(action_audit)


@responses.activate
@mock.patch.object(
    ActionsResource,
    '_exhume_date',
    return_value=datetime(2017, 9, 22, 22, 16, 14))
@patch('logging.Logger.info')
def test_invoke_airflow_dag_success(mock_info, mock_exhume_date):
    act_resource = ActionsResource()
    dag_id = 'test_dag_id'
    action = {'id': '123', 'user': 'unittester'}
    CONF = cfg.CONF
    web_server_url = CONF.base.web_server
    conf_value = {'action': action}
    log_string = 'Created <DagRun deploy_site @ 2017-09-22 22:16:14: man'
    responses.add(
        method='POST',
        url='{}api/experimental/dags/{}/dag_runs'.format(
            web_server_url, dag_id),
        body=json.dumps({'message': log_string}),
        status=200,
        content_type='application/json')

    result = act_resource.invoke_airflow_dag(dag_id, action, context)
    mock_exhume_date.assert_called_with(dag_id, log_string)
    assert result == '2017-09-22T22:16:14'


@responses.activate
@patch('logging.Logger.info')
def test_invoke_airflow_dag_errors(mock_info):
    act_resource = ActionsResource()
    dag_id = 'test_dag_id'
    action = {'id': '123', 'user': 'unittester'}
    web_server_url = CONF.base.web_server
    conf_value = {'action': action}
    responses.add(
        method='POST',
        url='{}api/experimental/dags/{}/dag_runs'.format(
            web_server_url, dag_id),
        body=json.dumps({
            "error": "not found"
        }),
        status=404,
        content_type='application/json')

    with pytest.raises(ApiError) as expected_exc:
        act_resource.invoke_airflow_dag(dag_id, action, context)
    mock_info.assert_called_with('Response code from Airflow trigger_dag: %s',
                                 404)
    assert 'Unable to complete request to Airflow' in str(expected_exc)
    assert 'Airflow could not be contacted properly by Shipyard' in str(
        expected_exc)

    with mock.patch.object(actions_api, 'CONF') as mock_conf:
        mock_conf.base.web_server = 'Error'
        with pytest.raises(ApiError) as expected_exc:
            act_resource.invoke_airflow_dag(dag_id, action, context)
        assert 'Unable to invoke workflow' in str(expected_exc)
        assert ('Airflow URL not found by Shipyard. Shipyard configuration is '
                'missing web_server value') in str(expected_exc)


def test_exhume_date():
    act_resource = ActionsResource()
    dag_id = 'test_dag_id'
    log_string = 'test_log_string'
    with pytest.raises(ApiError) as expected_exc:
        act_resource._exhume_date(dag_id, log_string)
    assert 'Unable to determine if workflow has started' in str(expected_exc)
    assert ('Airflow has not responded with parseable output. Shipyard is '
            'unable to determine run timestamp') in str(expected_exc)

    dag_id = 'deploy_site'
    log_string = 'Created <DagRun deploy_site @ 2017-09-22 22:16:14: man'
    result = act_resource._exhume_date(dag_id, log_string)
    assert result == datetime(2017, 9, 22, 22, 16, 14)

    log_string = 'Created <DagRun deploy_site @ test'
    with pytest.raises(ApiError) as expected_exc:
        act_resource._exhume_date(dag_id, log_string)
    assert 'Unable to determine if workflow has started' in str(expected_exc)
    assert (
        'Airflow has not responded with parseable output. Shipyard is unable '
        'to determine run timestamp') in str(expected_exc)


@mock.patch.object(ConfigdocsHelper, 'get_revision_id', return_value=7)
def test_get_committed_design_version(*args):
    act_resource = ActionsResource()
    act_resource.configdocs_helper = ConfigdocsHelper(ShipyardRequestContext())
    assert act_resource.get_committed_design_version() == 7


@mock.patch.object(ConfigdocsHelper, 'get_revision_id', return_value=None)
def test_get_committed_design_version_missing(*args):
    act_resource = ActionsResource()
    act_resource.configdocs_helper = ConfigdocsHelper(
        ShipyardRequestContext()
    )
    assert act_resource.get_committed_design_version() is None
