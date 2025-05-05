# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
from datetime import timedelta

import pendulum

from airflow.sdk import DAG

try:
    from common_step_factory import CommonStepFactory
except ImportError:
    from shipyard_airflow.dags.common_step_factory import CommonStepFactory
"""test site"""

PARENT_DAG_NAME = 'test_site'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.now('UTC').subtract(days=1),
    'email': [''],
    'email_on_failure': False,
    'email_on_retry': False,
    'provide_context': True,
    'retries': 0,
    'retry_delay': timedelta(seconds=30),
}

dag = DAG(PARENT_DAG_NAME, default_args=default_args, schedule=None)

step_factory = CommonStepFactory(parent_dag_name=PARENT_DAG_NAME,
                                 dag=dag,
                                 default_args=default_args,
                                 action_type='site')

action_xcom = step_factory.get_action_xcom()
preflight = step_factory.get_preflight()
deployment_configuration = step_factory.get_deployment_configuration()
test_releases = step_factory.get_armada_test_releases()

# DAG Wiring
preflight.set_upstream(action_xcom)
deployment_configuration.set_upstream(action_xcom)
test_releases.set_upstream([deployment_configuration, preflight])
