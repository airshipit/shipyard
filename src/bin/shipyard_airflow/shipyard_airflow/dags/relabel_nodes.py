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
"""relabel_nodes

The top-level orchestration DAG for updating only the node labels
using the Undercloud platform.
"""

PARENT_DAG_NAME = 'relabel_nodes'

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
                                 action_type='targeted')

# create steps
action_xcom = step_factory.get_action_xcom()
concurrency_check = step_factory.get_concurrency_check()
preflight = step_factory.get_preflight()
get_rendered_doc = step_factory.get_get_rendered_doc()
deployment_configuration = step_factory.get_deployment_configuration()
validate_site_design = step_factory.get_validate_site_design()
relabel_nodes = step_factory.get_relabel_nodes()

# DAG Wiring
concurrency_check.set_upstream(action_xcom)
preflight.set_upstream(concurrency_check)
get_rendered_doc.set_upstream(preflight)
deployment_configuration.set_upstream(get_rendered_doc)
validate_site_design.set_upstream(deployment_configuration)
relabel_nodes.set_upstream(validate_site_design)
