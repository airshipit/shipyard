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
    from validate_site_design import BAREMETAL
except ImportError:
    from shipyard_airflow.dags.common_step_factory import CommonStepFactory
    from shipyard_airflow.dags.validate_site_design import BAREMETAL

"""redeploy_server

The top-level orchestration DAG for redeploying server(s).
"""

PARENT_DAG_NAME = 'redeploy_server'

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
                                 action_type='targeted')


action_xcom = step_factory.get_action_xcom()
concurrency_check = step_factory.get_concurrency_check()
deployment_configuration = step_factory.get_deployment_configuration()
validate_site_design = step_factory.get_validate_site_design(
    targets=[BAREMETAL]
)
# TODO(bryan-strassner): When the rest of the necessary functionality is in
#     place, this step may need to be replaced with the guarded version of
#     destroying servers.
#     For now, this is the unguarded action, which will tear down the server
#     without concern for any workload.
destroy_server = step_factory.get_unguarded_destroy_servers()
drydock_build = step_factory.get_drydock_build()

# DAG Wiring
deployment_configuration.set_upstream(action_xcom)
validate_site_design.set_upstream([
    concurrency_check,
    deployment_configuration
])
destroy_server.set_upstream(validate_site_design)
drydock_build.set_upstream(destroy_server)
