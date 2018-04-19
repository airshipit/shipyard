# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
### Airflow Task State Sample Dag
"""
import airflow
from airflow import DAG
from airflow.operators import TaskStateOperator
from airflow.operators.bash_operator import BashOperator
from datetime import timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG('airflow_task_state',
          default_args=default_args,
          schedule_interval=None)

# Get Task State
t1 = TaskStateOperator(
    task_id='airflow_task_state',
    airflow_dag_id='openstack_cli',
    airflow_task_id='endpoint_list_task',
    airflow_execution_date='2017-07-02T21:30:33.519582',
    dag=dag)

# Use XCOM to Retrieve Task State
t2 = BashOperator(
    task_id='pull',
    bash_command=("echo {{ ti.xcom_pull(task_ids='airflow_task_state',"
                  " key='task_state') }}"),
    xcom_push=True,
    dag=dag)

t2.set_upstream(t1)
