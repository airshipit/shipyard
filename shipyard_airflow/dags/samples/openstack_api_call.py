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
### Openstack CLI Sample Dag
"""
import airflow
from airflow import DAG
from airflow.operators import OpenStackOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


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

dag = DAG('openstack_cli', default_args=default_args, schedule_interval=None)

# print_date
t1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag)

## Note that the openrc.sh file needs to be placed on a volume that can be
## accessed by the containers

# openstack endpoint list
t2 = OpenStackOperator(
    task_id='endpoint_list_task',
    openrc_file='/usr/local/airflow/dags/openrc.sh',
    openstack_command=['openstack', 'endpoint', 'list'],
    dag=dag)

# openstack service list
t3 = OpenStackOperator(
    task_id='service_list_task',
    openrc_file='/usr/local/airflow/dags/openrc.sh',
    openstack_command=['openstack', 'service', 'list'],
    dag=dag)

# openstack server list
t4 = OpenStackOperator(
    task_id='server_list_task',
    openrc_file='/usr/local/airflow/dags/openrc.sh',
    openstack_command=['openstack', 'server', 'list'],
    dag=dag)

# openstack network list
t5 = OpenStackOperator(
    task_id='network_list_task',
    openrc_file='/usr/local/airflow/dags/openrc.sh',
    openstack_command=['openstack', 'network', 'list'],
    dag=dag)

t2.set_upstream(t1)
t3.set_upstream(t1)
t4.set_upstream(t1)
t5.set_upstream(t1)

