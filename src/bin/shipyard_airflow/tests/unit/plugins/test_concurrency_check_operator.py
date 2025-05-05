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
from unittest import mock

import pytest
from shipyard_airflow.plugins import concurrency_check_operator as operator
from shipyard_airflow.plugins.concurrency_check_operator import (
    ConcurrencyCheckOperator
)
from airflow.exceptions import AirflowException

COLOR_SETS = [
    set(['blue', 'green']),
    set(['blue', 'purple']),
    set(['red', 'purple']),
    set(['red', 'orange']),
    set(['yellow', 'green']),
    set(['yellow', 'orange']),
]

CONFLICT_SET = set(['cow', 'monkey', 'chicken'])


def test_find_conflicting_dag_set():
    """
    Ensure that the right values are determined by find_conflicting_dag_set
    """
    # Should not be found in the default set - no conflicts
    assert not operator.find_conflicting_dag_set("this_is_completely_cheese")

    # Check for contents vs the COLOR_SETS
    not_in_green_response_set = set(['purple', 'red', 'orange'])
    response_set = operator.find_conflicting_dag_set(
        dag_name='green', conflicting_dag_sets=COLOR_SETS)
    assert 'blue' in response_set
    assert 'yellow' in response_set
    assert not_in_green_response_set.isdisjoint(response_set)
    assert len(response_set) == 2


def get_executing_dags_stub_running_twice():
    return [
        ('buffalo', 'now'),
        ('buffalo', 'earlier'),
        ('squirrel', 'ages ago'),
    ]


def get_executing_dags_stub():
    return [
        ('buffalo', 'now'),
        ('chicken', 'earlier'),
        ('monkey', 'ages ago'),
    ]


def get_executing_dags_stub_no_conflicts():
    return [
        ('buffalo', 'now'),
        ('hedgehog', 'earlier'),
        ('panda', 'ages ago'),
    ]


def test_find_conflicting_dag():
    """
    Ensure that:
    1) responds with a found conflict
    2) responds None if there is no conflict
    3) responds with the dag_id_to_check being searched for if it is running
       more than once.
    """
    cco = ConcurrencyCheckOperator(
        conflicting_dag_set=CONFLICT_SET,
        task_id='bogus')

    # no conflicts
    cco.get_executing_dags = get_executing_dags_stub_no_conflicts
    assert cco.find_conflicting_dag('buffalo') is None

    # self is running twice
    cco.get_executing_dags = get_executing_dags_stub_running_twice
    assert cco.find_conflicting_dag('buffalo') != 'squirrel'
    assert cco.find_conflicting_dag('buffalo') == 'buffalo'

    # a conflict from the list
    cco.get_executing_dags = get_executing_dags_stub
    assert cco.find_conflicting_dag('buffalo') != 'monkey'
    assert cco.find_conflicting_dag('buffalo') == 'chicken'


@mock.patch('shipyard_airflow.plugins.concurrency_check_operator.XcomPusher')
def test_execute_exception(xcom_pusher):
    """
    Run the whole execute function for testing
    """
    cco = ConcurrencyCheckOperator(
        conflicting_dag_set=CONFLICT_SET,
        task_id='bogus')
    # dag_id of cow should cause monkey to conflict.
    cco.check_dag_id = 'cow'
    cco.get_executing_dags = get_executing_dags_stub
    try:
        context = {'task_instance': None}
        cco.execute(context)
        pytest.fail('AirflowException should have been raised')
    except AirflowException as airflow_exception:
        assert 'Aborting run' in airflow_exception.args[0]


@mock.patch('shipyard_airflow.plugins.concurrency_check_operator.XcomPusher')
def test_execute_success(xcom_pusher):
    """
    Run the whole execute function for testing - successfully!
    """
    cco = ConcurrencyCheckOperator(
        conflicting_dag_set=set(['car', 'truck']),
        task_id='bogus')

    # dag_id of airplane should have no conflicts
    cco.check_dag_id = 'airplane'
    cco.get_executing_dags = get_executing_dags_stub
    try:
        context = {'task_instance': None}
        cco.execute(context)
        assert True
    except AirflowException:
        pytest.fail('AirflowException should not have been raised')
