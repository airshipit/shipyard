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
except ImportError:
    from shipyard_airflow.dags.common_step_factory import CommonStepFactory

"""update_site

The top-level orchestration DAG for updating a site using the Undercloud
platform.

TODO: We will disable pre-flight checks for now and will revisit it at
      a later date. The pre-flight checks will be more targeted in the
      case of 'update_site' and will include specific checks on things
      like coredns, calico and ceph.
"""
PARENT_DAG_NAME = 'update_site'

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
                                 default_args=default_args,
                                 action_type='site')

action_xcom = step_factory.get_action_xcom()
concurrency_check = step_factory.get_concurrency_check()
preflight = step_factory.get_preflight()
get_rendered_doc = step_factory.get_get_rendered_doc()
deployment_configuration = step_factory.get_deployment_configuration()
validate_site_design = step_factory.get_validate_site_design()
drydock_build = step_factory.get_drydock_build()
armada_build = step_factory.get_armada_build()
decide_airflow_upgrade = step_factory.get_decide_airflow_upgrade()
upgrade_airflow = step_factory.get_upgrade_airflow()
skip_upgrade_airflow = step_factory.get_skip_upgrade_airflow()
create_action_tag = step_factory.get_create_action_tag()

# DAG Wiring
preflight.set_upstream(action_xcom)
get_rendered_doc.set_upstream(action_xcom)
deployment_configuration.set_upstream(action_xcom)
validate_site_design.set_upstream([
    preflight,
    get_rendered_doc,
    concurrency_check,
    deployment_configuration
])
drydock_build.set_upstream(validate_site_design)
armada_build.set_upstream(drydock_build)
decide_airflow_upgrade.set_upstream(armada_build)
decide_airflow_upgrade.set_downstream([
    upgrade_airflow,
    skip_upgrade_airflow
])
create_action_tag.set_upstream([
    upgrade_airflow,
    skip_upgrade_airflow
])
