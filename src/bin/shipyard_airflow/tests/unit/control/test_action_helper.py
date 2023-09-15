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
""" Tests for the action_helper.py module """

from unittest.mock import patch
import yaml

from shipyard_airflow.control.helpers import action_helper
from shipyard_airflow.control.helpers.design_reference_helper import (
    DesignRefHelper
)


def get_repeated_steps():
    """Returns a list of fake step dictionaries with repeated steps (tries)

    For use in testing getting the latest of a step
    Currently, for tests that use this, the only thing that matters is the
    task ID and the try number. If this function gets used by more/future tests
    more data may need to be added

    task_A tries: 1, 2, 3
    task_B tries: 1
    task_C tries: 1, 2
    task_D tries: 1
    task_E tries: 1

    :returns: A list of fake (and incomplete) step dictionaries, some of which
              are repeated across multiple tries
    :rtype: list
    """
    return [
        {
            'task_id': 'task_A',
            'try_number': 1
        },
        {
            'task_id': 'task_A',
            'try_number': 2
        },
        {
            'task_id': 'task_A',
            'try_number': 3
        },
        {
            'task_id': 'task_B',
            'try_number': 1
        },
        {
            'task_id': 'task_C',
            'try_number': 2
        },
        {
            'task_id': 'task_C',
            'try_number': 1
        },
        {
            'task_id': 'task_D',
            'try_number': 1
        },
        {
            'task_id': 'task_E',
            'try_number': 1
        }
    ]


def get_fake_latest_step_dict_failed():
    """Make a fake dictionary of "latest" steps that represent a failed dag

    The only key required by the tests calling this function is "state", so
    the steps contained in the returned dict are incomplete

    :returns: A dictionary of "latest" steps that represent a failed dag
    :rtype: dict
    """
    return {
        'armada_build.armada_post_apply': {'state': 'failed'},
        'arbitrary_step': {'state': 'success'},
        'another_arbitrary_step': {'state': 'running'},
        'upgrade_airflow': {'state': 'success'},
        'concurrency_check': {'state': 'success'}
    }


def get_fake_latest_step_dict_running():
    """Make a fake dictionary of "latest" steps that represent a running dag

    The only key required by the tests calling this function is "state", so
    the steps contained in the returned dict are incomplete

    :returns: A dictionary of "latest" steps that represent a running dag
    :rtype: dict
    """
    return {
        'armada_build': {'state': 'queued'},
        'arbitrary_step': {'state': 'success'},
        'another_arbitrary_step': {'state': 'running'},
        'upgrade_airflow': {'state': 'running'},
        'concurrency_check': {'state': 'success'}
    }


def get_fake_latest_step_dict_successful():
    """Make a fake dictionary of "latest" steps that represent a successful dag

    The only key required by the tests calling this function is "state", so
    the steps contained in the returned dict are incomplete

    :returns: A dictionary of "latest" steps that represent a successful dag
    :rtype: dict
    """
    return {
        'armada_build': {'state': 'success'},
        'arbitrary_step': {'state': 'success'},
        'another_arbitrary_step': {'state': 'success'},
        'upgrade_airflow': {'state': 'skipped'},
        'concurrency_check': {'state': 'success'}
    }


def get_fake_latest_step_dict_unknown():
    """Make a fake dictionary of "latest" steps that represent a dag of unknown
    result

    The only key required by the tests calling this function is "state", so
    the steps contained in the returned dict are incomplete

    :returns: A dictionary of "latest" steps that represent a dag of unknown
              result
    :rtype: dict
    """
    return {
        'armada_build': {'state': 'success'},
        'arbitrary_step': {'state': 'what'},
        'another_arbitrary_step': {'state': 'are'},
        'upgrade_airflow': {'state': 'these'},
        'concurrency_check': {'state': 'states?'}
    }


def test_determine_lifecycle():
    dag_statuses = [
        {'input': 'queued', 'expected': 'Pending'},
        {'input': 'ShUTdown', 'expected': 'Failed'},
        {'input': 'RUNNING', 'expected': 'Processing'},
        {'input': 'None', 'expected': 'Pending'},
        {'input': None, 'expected': 'Pending'},
        {'input': 'bogusBroken', 'expected': 'Unknown (bogusBroken)'},
    ]
    for status_pair in dag_statuses:
        assert(status_pair['expected'] ==
               action_helper.determine_lifecycle(status_pair['input']))


def test_get_step():
    # Set up actions helper
    action_id = '01CPV581B0CM8C9CA0CFRNVPPY'  # id in db
    actions = yaml.safe_load("""
---
  - id: 01CPV581B0CM8C9CA0CFRNVPPY
    name: update_software
    parameters: {}
    dag_id: update_software
    dag_execution_date: 2018-09-07T23:18:04
    user: admin
    datetime: 2018-09-07 23:18:04.38546+00
    context_marker: 10447c79-b02c-4dfd-a9e8-1362842f029d
...
""")
    action_helper.ActionsHelper._get_action_db = lambda \
            self, action_id: actions[0]

    tasks = yaml.safe_load("""
---
  - task_id: armada_post_apply
    dag_id: update_software.armada_build
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:48:25.884615
    end_date: 2018-09-07 23:48:50.552757
    duration: 24.668142
    state: success
    try_number: 1
    hostname: airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 13
    pool:
    queue: default
    priority_weight: 2
    operator: ArmadaPostApplyOperator
    queued_dttm:
    pid: 329
    max_tries: 3
  - task_id: armada_post_apply
    dag_id: update_software.armada_build
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:48:25.884615
    end_date: 2018-09-07 23:48:50.552757
    duration: 24.668142
    state: success
    try_number: 2
    hostname: airflow-worker-1.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 13
    pool:
    queue: default
    priority_weight: 2
    operator: ArmadaPostApplyOperator
    queued_dttm:
    pid: 329
    max_tries: 3
  - task_id: armada_get_releases
    dag_id: update_software.armada_build
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:48:59.024696
    end_date: 2018-09-07 23:49:01.471963
    duration: 2.447267
    state: success
    try_number: 1
    hostname: airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 14
    pool:
    queue: default
    priority_weight: 1
    operator: ArmadaGetReleasesOperator
    queued_dttm:
    pid: 365
    max_tries: 0
  - task_id: armada_build
    dag_id: update_software
    execution_date: 2018-09-07 23:18:04
    start_date: 2018-09-07 23:18:47.447987
    end_date: 2018-09-07 23:49:02.397515
    duration: 1814.949528
    state: success
    try_number: 1
    hostname: airflow-worker-0.airflow-worker-discovery.ucp.svc.cluster.local
    unixname: airflow
    job_id: 9
    pool:
    queue: default
    priority_weight: 5
    operator: SubDagOperator
    queued_dttm: 2018-09-07 23:18:45.772501
    pid: 221
    max_tries: 0
...
""")
    action_helper.ActionsHelper._get_tasks_db = lambda \
            self, dag_id, execution_date: tasks
    actions_helper = action_helper.ActionsHelper(action_id=action_id)

    # Retrieve step
    step_id = 'armada_post_apply'  # task_id in db

    # test backward compatibility with no additional param
    step = actions_helper.get_step(step_id)
    assert(step['hostname'].startswith('airflow-worker-0'))

    # test explicit None
    try_number = None
    step = actions_helper.get_step(step_id, try_number)
    assert(step['hostname'].startswith('airflow-worker-0'))

    # test try_number associated with 0 worker
    try_number = 1
    step = actions_helper.get_step(step_id, try_number)
    assert(step['hostname'].startswith('airflow-worker-0'))

    # test try_number associated with 1 worker
    try_number = 2
    step = actions_helper.get_step(step_id, try_number)
    assert(step['hostname'].startswith('airflow-worker-1'))


@patch('shipyard_airflow.control.helpers.deckhand_client.DeckhandClient.'
       'get_path')
@patch('shipyard_airflow.control.helpers.design_reference_helper.'
       'DesignRefHelper.get_design_reference_href', return_value='href')
def test_get_deployment_status_no_action_helper_completed_failed(get_href,
                                                                 get_path):
    action = {
        'committed_rev_id': 'rev_id',
        'context_marker': 'markofcontext',
        'dag_status': 'FAILED',
        'id': 'action_id',
        'timestamp': 'my_timestamp',
        'user': 'cool-person'
    }
    expected_data = {
        'status': 'completed',
        'results': 'failed',
        'context-marker': action['context_marker'],
        'action': action['id'],
        'document_url': 'href',
        'user': action['user'],
        'date': action['timestamp']
    }

    deployment_status = action_helper.get_deployment_status(action)
    assert deployment_status['status'] == expected_data['status']
    assert deployment_status['results'] == expected_data['results']
    assert (deployment_status['context-marker'] ==
            expected_data['context-marker'])
    assert deployment_status['action'] == expected_data['action']
    assert deployment_status['document_url'] == expected_data['document_url']
    assert deployment_status['user'] == expected_data['user']
    assert deployment_status['date'] == expected_data['date']
    get_href.assert_called_once_with(action['committed_rev_id'])
    assert get_path.called  # This means we created a DesignRefHelper object


@patch('shipyard_airflow.control.helpers.deckhand_client.DeckhandClient.'
       'get_path')
@patch('shipyard_airflow.control.helpers.design_reference_helper.'
       'DesignRefHelper.get_design_reference_href', return_value='href')
def test_get_deployment_status_no_action_helper_completed_success(get_href,
                                                                  get_path):
    action = {
        'committed_rev_id': 'rev_id',
        'context_marker': 'markofcontext',
        'dag_status': 'SUCCESS',
        'id': 'action_id',
        'timestamp': 'my_timestamp',
        'user': 'cool-person'
    }
    expected_data = {
        'status': 'completed',
        'results': 'successful',
        'context-marker': action['context_marker'],
        'action': action['id'],
        'document_url': 'href',
        'user': action['user'],
        'date': action['timestamp']
    }

    deployment_status = action_helper.get_deployment_status(action)
    assert deployment_status['status'] == expected_data['status']
    assert deployment_status['results'] == expected_data['results']
    assert (deployment_status['context-marker'] ==
            expected_data['context-marker'])
    assert deployment_status['action'] == expected_data['action']
    assert deployment_status['document_url'] == expected_data['document_url']
    assert deployment_status['user'] == expected_data['user']
    assert deployment_status['date'] == expected_data['date']
    get_href.assert_called_once_with(action['committed_rev_id'])
    assert get_path.called  # This means we created a DesignRefHelper object


@patch.object(action_helper.ActionsHelper,
              'get_result_from_dag_steps',
              return_value='result')
@patch('shipyard_airflow.control.helpers.deckhand_client.DeckhandClient.'
       'get_path')
@patch('shipyard_airflow.control.helpers.design_reference_helper.'
       'DesignRefHelper.get_design_reference_href', return_value='href')
def test_get_deployment_status_use_action_helper(get_href,
                                                 get_path,
                                                 get_result):
    action = {
        'committed_rev_id': 'rev_id',
        'context_marker': 'markofcontext',
        'dag_status': 'ASDFJKL:',
        'id': 'action_id',
        'timestamp': 'my_timestamp',
        'user': 'cool-person'
    }
    expected_data = {
        'status': 'running',
        'results': 'result',
        'context-marker': action['context_marker'],
        'action': action['id'],
        'document_url': 'href',
        'user': action['user'],
        'date': action['timestamp']
    }

    deployment_status = action_helper.get_deployment_status(action)
    assert deployment_status['status'] == expected_data['status']
    assert deployment_status['results'] == expected_data['results']
    assert (deployment_status['context-marker'] ==
            expected_data['context-marker'])
    assert deployment_status['action'] == expected_data['action']
    assert deployment_status['document_url'] == expected_data['document_url']
    assert deployment_status['user'] == expected_data['user']
    assert deployment_status['date'] == expected_data['date']
    get_href.assert_called_once_with(action['committed_rev_id'])
    assert get_result.called
    assert get_path.called  # This means we created a DesignRefHelper object


@patch.object(action_helper.ActionsHelper,
              'get_result_from_dag_steps',
              return_value='result')
@patch('shipyard_airflow.control.helpers.deckhand_client.DeckhandClient.'
       'get_path')
@patch('shipyard_airflow.control.helpers.design_reference_helper.'
       'DesignRefHelper.get_design_reference_href', return_value='href')
def test_get_deployment_status_use_action_helper_force_completed(get_href,
                                                                 get_path,
                                                                 get_result):
    action = {
        'committed_rev_id': 'rev_id',
        'context_marker': 'markofcontext',
        'dag_status': 'ASDFJKL:',
        'id': 'action_id',
        'timestamp': 'my_timestamp',
        'user': 'cool-person'
    }
    expected_data = {
        'status': 'completed',
        'results': 'result',
        'context-marker': action['context_marker'],
        'action': action['id'],
        'document_url': 'href',
        'user': action['user'],
        'date': action['timestamp']
    }

    deployment_status = action_helper.get_deployment_status(action, True)
    assert deployment_status['status'] == expected_data['status']
    assert deployment_status['results'] == expected_data['results']
    assert (deployment_status['context-marker'] ==
            expected_data['context-marker'])
    assert deployment_status['action'] == expected_data['action']
    assert deployment_status['document_url'] == expected_data['document_url']
    assert deployment_status['user'] == expected_data['user']
    assert deployment_status['date'] == expected_data['date']
    get_href.assert_called_once_with(action['committed_rev_id'])
    assert get_result.called
    assert get_path.called  # This means we created a DesignRefHelper object


@patch.object(action_helper.ActionsHelper, '_get_action_info')
@patch.object(action_helper.ActionsHelper, '_get_all_steps',
              return_value=get_repeated_steps())
def test__get_latest_steps(get_all_steps, get_action_info):
    helper = action_helper.ActionsHelper(action_id='irrelevant')
    latest_steps_dict = helper._get_latest_steps()
    assert latest_steps_dict['task_A']['try_number'] == 3
    assert latest_steps_dict['task_B']['try_number'] == 1
    assert latest_steps_dict['task_C']['try_number'] == 2
    assert latest_steps_dict['task_D']['try_number'] == 1
    assert latest_steps_dict['task_E']['try_number'] == 1
    assert get_all_steps.called
    assert get_action_info.called


@patch.object(action_helper.ActionsHelper, '_get_action_info')
@patch.object(action_helper.ActionsHelper, '_get_latest_steps',
              return_value=get_fake_latest_step_dict_successful())
def test_get_result_from_dag_steps_success(get_latest_steps, get_action_info):
    helper = action_helper.ActionsHelper(action_id='irrelevant')
    result = helper.get_result_from_dag_steps()
    assert result == 'successful'
    assert get_latest_steps.called
    assert get_action_info.called


@patch.object(action_helper.ActionsHelper, '_get_action_info')
@patch.object(action_helper.ActionsHelper, '_get_latest_steps',
              return_value=get_fake_latest_step_dict_failed())
def test_get_result_from_dag_steps_failed(get_latest_steps, get_action_info):
    helper = action_helper.ActionsHelper(action_id='irrelevant')
    result = helper.get_result_from_dag_steps()
    assert result == 'failed'
    assert get_latest_steps.called
    assert get_action_info.called


@patch.object(action_helper.ActionsHelper, '_get_action_info')
@patch.object(action_helper.ActionsHelper, '_get_latest_steps',
              return_value=get_fake_latest_step_dict_running())
def test_get_result_from_dag_steps_running(get_latest_steps, get_action_info):
    helper = action_helper.ActionsHelper(action_id='irrelevant')
    result = helper.get_result_from_dag_steps()
    assert result == 'pending'
    assert get_latest_steps.called
    assert get_action_info.called


@patch('logging.Logger.warning')
@patch.object(action_helper.ActionsHelper, '_get_action_info')
@patch.object(action_helper.ActionsHelper, '_get_latest_steps',
              return_value=get_fake_latest_step_dict_unknown())
def test_get_result_from_dag_steps_unknown(get_latest_steps,
                                           get_action_info,
                                           log_warning_patch):
    helper = action_helper.ActionsHelper(action_id='irrelevant')
    result = helper.get_result_from_dag_steps()
    assert result == 'unknown'
    assert get_latest_steps.called
    assert get_action_info.called
    # Each critical step that had an unknown state should log a warning:
    assert log_warning_patch.call_count == 1
