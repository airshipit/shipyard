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

import airflow
from airflow import DAG

try:
    from common_step_factory import CommonStepFactory
    from validate_site_design import SOFTWARE
except ImportError:
    from shipyard_airflow.dags.common_step_factory import CommonStepFactory
    from shipyard_airflow.dags.validate_site_design import SOFTWARE

"""update_software

The top-level orchestration DAG for updating only the software components
using the Undercloud platform.
"""
PARENT_DAG_NAME = 'update_software'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(1),
    'email': [''],
    'email_on_failure': False,
    'email_on_retry': False,
    'provide_context': True,
    'retries': 0,
    'retry_delay': timedelta(seconds=30),
}

dag = DAG(PARENT_DAG_NAME, default_args=default_args, schedule_interval=None)

step_factory = CommonStepFactory(parent_dag_name=PARENT_DAG_NAME,
                                 dag=dag,
                                 default_args=default_args)

action_xcom = step_factory.get_action_xcom()
concurrency_check = step_factory.get_concurrency_check()
deployment_configuration = step_factory.get_deployment_configuration()
validate_site_design = step_factory.get_validate_site_design(
    targets=[SOFTWARE]
)
armada_build = step_factory.get_armada_build()
decide_airflow_upgrade = step_factory.get_decide_airflow_upgrade()
upgrade_airflow = step_factory.get_upgrade_airflow()
skip_upgrade_airflow = step_factory.get_skip_upgrade_airflow()
create_action_tag = step_factory.get_create_action_tag()

# DAG Wiring
deployment_configuration.set_upstream(action_xcom)
validate_site_design.set_upstream([
    concurrency_check,
    deployment_configuration
])
armada_build.set_upstream(validate_site_design)
decide_airflow_upgrade.set_upstream(armada_build)
decide_airflow_upgrade.set_downstream([
    upgrade_airflow,
    skip_upgrade_airflow
])
create_action_tag.set_upstream([
    upgrade_airflow,
    skip_upgrade_airflow
])
