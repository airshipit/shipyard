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

from airflow.models import DAG
from airflow.operators import ArmadaGetReleasesOperator
from airflow.operators import ArmadaGetStatusOperator
from airflow.operators import ArmadaPostApplyOperator

from config_path import config_path


def deploy_site_armada(parent_dag_name, child_dag_name, args):
    '''
    Armada Subdag
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    # Get Tiller Status
    armada_get_status = ArmadaGetStatusOperator(
        task_id='armada_get_status',
        shipyard_conf=config_path,
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Armada Apply
    armada_post_apply = ArmadaPostApplyOperator(
        task_id='armada_post_apply',
        shipyard_conf=config_path,
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        retries=3,
        dag=dag)

    # Get Helm Releases
    armada_get_releases = ArmadaGetReleasesOperator(
        task_id='armada_get_releases',
        shipyard_conf=config_path,
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Define dependencies
    armada_post_apply.set_upstream(armada_get_status)
    armada_get_releases.set_upstream(armada_post_apply)

    return dag
