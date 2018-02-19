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

from airflow.models import DAG
from airflow.operators import ArmadaOperator
from airflow.operators import DeckhandValidateSiteDesignOperator
from airflow.operators import DryDockOperator

from config_path import config_path


def validate_site_design(parent_dag_name, child_dag_name, args):
    '''
    Subdag to delegate design verification to the UCP components
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    deckhand_validate_docs = DeckhandValidateSiteDesignOperator(
        task_id='deckhand_validate_site_design',
        shipyard_conf=config_path,
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    drydock_validate_docs = DryDockOperator(
        task_id='drydock_validate_site_design',
        shipyard_conf=config_path,
        action='validate_site_design',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        retries=3,
        dag=dag)

    armada_validate_docs = ArmadaOperator(
        task_id='armada_validate_site_design',
        shipyard_conf=config_path,
        action='validate_site_design',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        retries=3,
        dag=dag)

    return dag
