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
import pendulum

from airflow.sdk import DAG
from datetime import timedelta
try:
    from airflow.operators import OpenStackOperator
    from config_path import config_path
except ImportError:
    from shipyard_airflow.plugins.openstack_operators import \
        OpenStackOperator
    from shipyard_airflow.dags.config_path import config_path

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.now('UTC').subtract(days=1),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG('openstack_cli', default_args=default_args, schedule=None)

# # Location of shiyard.conf
# config_path = '/usr/local/airflow/plugins/shipyard.conf'

# Note that the shipyard.conf file needs to be placed on a volume
# that can be accessed by the containers

# openstack endpoint list
t1 = OpenStackOperator(task_id='endpoint_list_task',
                       shipyard_conf=config_path,
                       openstack_command=['openstack', 'endpoint', 'list'],
                       dag=dag)

# openstack service list
t2 = OpenStackOperator(task_id='service_list_task',
                       shipyard_conf=config_path,
                       openstack_command=['openstack', 'service', 'list'],
                       dag=dag)

# openstack server list
t3 = OpenStackOperator(task_id='server_list_task',
                       shipyard_conf=config_path,
                       openstack_command=['openstack', 'server', 'list'],
                       dag=dag)

t2.set_upstream(t1)
t3.set_upstream(t2)
