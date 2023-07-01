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

import arrow

from shipyard_airflow.control.helpers.workflow_helper import (
    WorkflowHelper
)


def test__add_id_to_run():
    """
    static method _add_id_to_run
    """
    assert WorkflowHelper._add_id_to_run(
        {'dag_id': 'aardvark', 'execution_date': '1924-04-12T05:34:01.222220'}
    )['workflow_id'] == 'aardvark__1924-04-12T05:34:01.222220'

    assert WorkflowHelper._add_id_to_run(
        {}
    )['workflow_id'] == 'None__None'


def test__split_workflow_id_to_dag_run():
    """
    static method _split_workflow_id_to_dag_run
    """
    assert WorkflowHelper._split_workflow_id_to_dag_run(
        'aardvark__1924-04-12T05:34:01.222220'
    )['dag_id'] == 'aardvark'

    assert WorkflowHelper._split_workflow_id_to_dag_run(
        'aar__dvark__1924-04-12T05:34:01.222220'
    )['dag_id'] == 'aar__dvark'

    assert WorkflowHelper._split_workflow_id_to_dag_run(
        'aardvark__1924-04-12T05:34:01.222220'
    )['execution_date'] == '1924-04-12T05:34:01.222220'

    assert WorkflowHelper._split_workflow_id_to_dag_run(
        'aar__dvark__1924-04-12T05:34:01.222220'
    )['execution_date'] == '1924-04-12T05:34:01.222220'


def test_validate_workflow_id():
    """
    static method validate_workflow_id
    """
    assert WorkflowHelper.validate_workflow_id(
        'aar__dvark__1924-04-12T05:34:01.222220'
    )

    assert not WorkflowHelper.validate_workflow_id(
        'aardvark_1924-04-12T05:34:01.222220'
    )

    assert not WorkflowHelper.validate_workflow_id(
        None
    )


def test__get_threshold_date():
    """
    static method _get_threshold_date
    """
    assert (
        arrow.utcnow().shift(days=-30).naive <=
        WorkflowHelper._get_threshold_date('turnip') <=
        arrow.utcnow().shift(days=-30).naive
    )

    assert (
        arrow.utcnow().shift(days=-30).naive <=
        WorkflowHelper._get_threshold_date(None) <=
        arrow.utcnow().shift(days=-30).naive
    )

    assert (
        WorkflowHelper._get_threshold_date('2017-10-09T10:00:00.000000') ==
        arrow.get('2017-10-09T10:00:00.00000').naive
    )

RUN_ID_ONE = "AAAAAAAAAAAAAAAAAAAAA"
RUN_ID_TWO = "BBBBBBBBBBBBBBBBBBBBB"
DATE_ONE = datetime(2017, 9, 13, 11, 13, 3, 57000)
DATE_TWO = datetime(2017, 9, 13, 11, 13, 5, 57000)

DAG_RUN_1 = {
    'dag_id': 'did2',
    'execution_date': DATE_ONE,
    'state': 'FAILED',
    'run_id': RUN_ID_TWO,
    'external_trigger': 'something',
    'start_date': DATE_ONE,
    'end_date': DATE_ONE
}


def test_get_workflow_list():
    """
    Tests the get_workflow_list method
    """
    helper = WorkflowHelper('')
    helper._get_all_dag_runs_db = lambda: [DAG_RUN_1, DAG_RUN_1, DAG_RUN_1]

    # Time includes items
    dag_list = helper.get_workflow_list(
        since_iso8601='2017-09-13T11:12:00.000000'
    )
    assert DAG_RUN_1 in dag_list
    assert len(dag_list) == 3

    # Time excludes items
    dag_list = helper.get_workflow_list(
        since_iso8601='2017-10-01T11:12:00.000000'
    )
    assert DAG_RUN_1 not in dag_list
    assert len(dag_list) == 0


TASK_LIST = [
    {
        'task_id': '1a',
        'dag_id': 'did2',
        'state': 'SUCCESS',
        'run_id': RUN_ID_ONE,
        'external_trigger': 'something',
        'start_date': DATE_ONE,
        'end_date': DATE_ONE,
        'duration': '20mins',
        'try_number': '1',
        'operator': 'smooth',
        'queued_dttm': DATE_ONE
    },
    {
        'task_id': '1b',
        'dag_id': 'did2',
        'state': 'SUCCESS',
        'run_id': RUN_ID_ONE,
        'external_trigger': 'something',
        'start_date': DATE_TWO,
        'end_date': DATE_TWO,
        'duration': '1minute',
        'try_number': '1',
        'operator': 'smooth',
        'queued_dttm': DATE_ONE
    },
    {
        'task_id': '1c',
        'dag_id': 'did2',
        'state': 'FAILED',
        'run_id': RUN_ID_ONE,
        'external_trigger': 'something',
        'start_date': DATE_TWO,
        'end_date': DATE_TWO,
        'duration': '1day',
        'try_number': '3',
        'operator': 'smooth',
        'queued_dttm': DATE_TWO
    }
]


def test_get_workflow():
    """
    Tests the get_workflow method
    """
    helper = WorkflowHelper('')
    helper._get_dag_run_like_id_db = lambda dag_id, execution_date: [DAG_RUN_1]
    helper._get_tasks_by_id_db = lambda dag_id, execution_date: TASK_LIST
    dag_detail = helper.get_workflow(
        workflow_id='dag_id__1957-03-14T12:12:12.000000'
    )
    assert dag_detail['dag_id'] == 'did2'
    assert len(dag_detail['steps']) == 3

    dag_detail = helper.get_workflow(
        workflow_id='NOTHING'
    )
    assert dag_detail == {}


DAG_RUN_SUB = {
    'dag_id': 'did2.didnt',
    'execution_date': DATE_ONE,
    'state': 'FAILED',
    'run_id': RUN_ID_TWO,
    'external_trigger': 'something',
    'start_date': DATE_ONE,
    'end_date': DATE_ONE
}


def test_get_workflow_subords():
    """
    Tests the get_workflow method
    """
    helper = WorkflowHelper('')
    helper._get_dag_run_like_id_db = (
        lambda dag_id, execution_date: [DAG_RUN_SUB, DAG_RUN_1]
    )
    helper._get_tasks_by_id_db = lambda dag_id, execution_date: TASK_LIST
    dag_detail = helper.get_workflow(
        workflow_id='dag_id__1957-03-14T12:12:12.000000'
    )
    assert dag_detail['dag_id'] == 'did2'
    assert len(dag_detail['sub_dags']) == 1
    assert dag_detail['sub_dags'][0]['dag_id'] == 'did2.didnt'
    assert len(dag_detail['steps']) == 3