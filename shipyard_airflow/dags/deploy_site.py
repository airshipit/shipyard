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

from datetime import timedelta

import airflow
from airflow import DAG
from dag_concurrency_check import dag_concurrency_check
from dag_concurrency_check import dag_concurrency_check_failure_handler
from preflight_checks import all_preflight_checks
from preflight_checks import preflight_failure_handler
from validate_site_design import validate_site_design
from validate_site_design import validate_site_design_failure_handler
from airflow.operators.subdag_operator import SubDagOperator
from airflow.operators import DeckhandOperator
from airflow.operators import PlaceholderOperator
from airflow.utils.trigger_rule import TriggerRule
'''
deploy_site is the top-level orchestration DAG for deploying a site using the
Undercloud platform.
'''

PARENT_DAG_NAME = 'deploy_site'
DAG_CONCURRENCY_CHECK_DAG_NAME = 'dag_concurrency_check'
CONCURRENCY_FAILURE_DAG_NAME = 'concurrency_check_failure_handler'
ALL_PREFLIGHT_CHECKS_DAG_NAME = 'preflight'
PREFLIGHT_FAILURE_DAG_NAME = 'preflight_failure_handler'
DECKHAND_GET_DESIGN_VERSION = 'deckhand_get_design_version'
VALIDATE_SITE_DESIGN_DAG_NAME = 'validate_site_design'
VALIDATION_FAILED_DAG_NAME = 'validate_site_design_failure_handler'
DECKHAND_MARK_LAST_KNOWN_GOOD = 'deckhand_mark_last_known_good'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(1),
    'email': [''],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(PARENT_DAG_NAME, default_args=default_args, schedule_interval=None)

concurrency_check = SubDagOperator(
    subdag=dag_concurrency_check(
        PARENT_DAG_NAME, DAG_CONCURRENCY_CHECK_DAG_NAME, args=default_args),
    task_id=DAG_CONCURRENCY_CHECK_DAG_NAME,
    dag=dag, )

concurrency_check_failure_handler = SubDagOperator(
    subdag=dag_concurrency_check_failure_handler(
        PARENT_DAG_NAME, CONCURRENCY_FAILURE_DAG_NAME, args=default_args),
    task_id=CONCURRENCY_FAILURE_DAG_NAME,
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag, )

preflight = SubDagOperator(
    subdag=all_preflight_checks(
        PARENT_DAG_NAME, ALL_PREFLIGHT_CHECKS_DAG_NAME, args=default_args),
    task_id=ALL_PREFLIGHT_CHECKS_DAG_NAME,
    dag=dag, )

preflight_failure = SubDagOperator(
    subdag=preflight_failure_handler(
        PARENT_DAG_NAME, PREFLIGHT_FAILURE_DAG_NAME, args=default_args),
    task_id=PREFLIGHT_FAILURE_DAG_NAME,
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag, )

get_design_version = DeckhandOperator(
    task_id=DECKHAND_GET_DESIGN_VERSION, dag=dag)

validate_site_design = SubDagOperator(
    subdag=validate_site_design(
        PARENT_DAG_NAME, VALIDATE_SITE_DESIGN_DAG_NAME, args=default_args),
    task_id=VALIDATE_SITE_DESIGN_DAG_NAME,
    dag=dag)

validate_site_design_failure = SubDagOperator(
    subdag=validate_site_design_failure_handler(
        dag.dag_id, VALIDATION_FAILED_DAG_NAME, args=default_args),
    task_id=VALIDATION_FAILED_DAG_NAME,
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag)

drydock_build = PlaceholderOperator(task_id='drydock_build', dag=dag)

drydock_failure_handler = PlaceholderOperator(
    task_id='drydock_failure_handler',
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag)

query_node_status = PlaceholderOperator(
    task_id='deployed_node_status', dag=dag)

nodes_not_healthy = PlaceholderOperator(
    task_id='deployed_nodes_not_healthy',
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag)

armada_build = PlaceholderOperator(task_id='armada_build', dag=dag)

armada_failure_handler = PlaceholderOperator(
    task_id='armada_failure_handler',
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag)

mark_last_known_good = DeckhandOperator(
    task_id=DECKHAND_MARK_LAST_KNOWN_GOOD, dag=dag)

# DAG Wiring
concurrency_check_failure_handler.set_upstream(concurrency_check)
preflight.set_upstream(concurrency_check)
preflight_failure.set_upstream(preflight)
get_design_version.set_upstream(preflight)
validate_site_design.set_upstream(get_design_version)
validate_site_design_failure.set_upstream(validate_site_design)
drydock_build.set_upstream(validate_site_design)
drydock_failure_handler.set_upstream(drydock_build)
query_node_status.set_upstream(drydock_build)
nodes_not_healthy.set_upstream(query_node_status)
armada_build.set_upstream(query_node_status)
armada_failure_handler.set_upstream(armada_build)
mark_last_known_good.set_upstream(armada_build)
