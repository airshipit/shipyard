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
### DryDock Operator Parent Dag
"""
import airflow
from airflow import DAG
from datetime import timedelta
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator
from drydock_operator_child import sub_dag

parent_dag_name = 'drydock_operator_parent'
child_dag_name = 'drydock_operator_child'

args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(1),
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
    'provide_context': True
}

main_dag = DAG(
    dag_id=parent_dag_name,
    default_args=args,
    schedule_interval=None,
    start_date=airflow.utils.dates.days_ago(1),
    max_active_runs=1
)

# Define push function to store the content of 'action' that is
# defined via 'dag_run' in XCOM so that it can be used by the
# DryDock Operators
def push(**kwargs):
    # Pushes action XCom
    kwargs['ti'].xcom_push(key='action',
                           value=kwargs['dag_run'].conf['action'])


action_xcom = PythonOperator(
    task_id='action_xcom', dag=main_dag, python_callable=push)

subdag = SubDagOperator(
    subdag=sub_dag(parent_dag_name, child_dag_name, args,
                   main_dag.schedule_interval),
    task_id=child_dag_name,
    default_args=args,
    dag=main_dag)

# Set dependencies
subdag.set_upstream(action_xcom)
