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

# Location of shiyard.conf
# Note that the shipyard.conf file needs to be placed on a volume
# that can be accessed by the containers
config_path = '/usr/local/airflow/plugins/shipyard.conf'


def deploy_site_armada(parent_dag_name, child_dag_name, args):
    '''
    Armada Subdag
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    # Create Armada Client
    armada_client = ArmadaOperator(
        task_id='create_armada_client',
        shipyard_conf=config_path,
        action='create_armada_client',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Get Tiller Status
    armada_status = ArmadaOperator(
        task_id='armada_status',
        shipyard_conf=config_path,
        action='armada_status',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Validate Armada YAMLs
    armada_validate = ArmadaOperator(
        task_id='armada_validate',
        shipyard_conf=config_path,
        action='armada_validate',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Armada Apply
    armada_apply = ArmadaOperator(
        task_id='armada_apply',
        shipyard_conf=config_path,
        action='armada_apply',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        retries=10,
        dag=dag)

    # Get Helm Releases
    armada_get_releases = ArmadaOperator(
        task_id='armada_get_releases',
        shipyard_conf=config_path,
        action='armada_get_releases',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Define dependencies
    armada_status.set_upstream(armada_client)
    armada_validate.set_upstream(armada_status)
    armada_apply.set_upstream(armada_validate)
    armada_get_releases.set_upstream(armada_apply)

    return dag
