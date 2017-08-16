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

import airflow
from airflow.models import DAG
from airflow.operators import PlaceholderOperator
from airflow.operators.dummy_operator import DummyOperator


def dag_concurrency_check(parent_dag_name, child_dag_name, args):
    '''
    dag_concurrency_check is a sub-DAG that will will allow for a DAG to
    determine if it is already running, and result in an error if so.
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    # TODO () Replace this operator with a real operator that will:
    # 1) Look for an instance of the parent_dag_name running currently in
    #    airflow
    # 2) Fail if the parent_dag_name is running
    # 3) Succeed if there are no instances of parent_dag_name running
    dag_concurrency_check_operator = PlaceholderOperator(
        task_id='dag_concurrency_check', dag=dag)

    return dag


def dag_concurrency_check_failure_handler(parent_dag_name, child_dag_name,
                                          args):
    '''
    Peforms the actions necessary when concurrency checks fail
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DummyOperator(
        task_id='dag_concurrency_check_failure_handler', dag=dag, )

    return dag
