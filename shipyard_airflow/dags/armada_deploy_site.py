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
from airflow.operators.subdag_operator import SubDagOperator

# Location of shiyard.conf
config_path = '/usr/local/airflow/plugins/shipyard.conf'

# Names used for sub-subdags in the armada site deployment subdag
CREATE_ARMADA_CLIENT_DAG_NAME = 'create_armada_client'
GET_ARMADA_STATUS_DAG_NAME = 'armada_status'
ARMADA_VALIDATE_DAG_NAME = 'armada_validate'
ARMADA_APPLY_DAG_NAME = 'armada_apply'
ARMADA_GET_RELEASES_DAG_NAME = 'armada_get_releases'


def get_armada_subdag_step(parent_dag_name, child_dag_name, args):
    '''
    Execute Armada Subdag
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    # Note that in the event where the 'deploy_site' Action is
    # triggered from Shipyard, the 'parent_dag_name' variable
    # gets assigned with 'deploy_site.create_armada_client'.
    # This is the name that we want to assign to the subdag so
    # that we can reference it for xcom. The name of the main
    # dag will be the front part of that value, i.e. 'deploy_site'.
    # Hence we will extract the front part and assign it to main_dag.
    # We will reuse this pattern for other Actions, e.g. update_site,
    # redeploy_site as well.
    operator = ArmadaOperator(
        task_id=child_dag_name,
        shipyard_conf=config_path,
        action=child_dag_name,
        main_dag_name=parent_dag_name[0:parent_dag_name.find('.')],
        sub_dag_name=parent_dag_name,
        dag=dag)

    return dag


def deploy_site_armada(parent_dag_name, child_dag_name, args):
    '''
    Puts into atomic unit
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    armada_client = SubDagOperator(
        subdag=get_armada_subdag_step(dag.dag_id,
                                      CREATE_ARMADA_CLIENT_DAG_NAME,
                                      args),
        task_id=CREATE_ARMADA_CLIENT_DAG_NAME,
        dag=dag)

    armada_status = SubDagOperator(
        subdag=get_armada_subdag_step(dag.dag_id,
                                      GET_ARMADA_STATUS_DAG_NAME,
                                      args),
        task_id=GET_ARMADA_STATUS_DAG_NAME,
        dag=dag)

    armada_validate = SubDagOperator(
        subdag=get_armada_subdag_step(dag.dag_id,
                                      ARMADA_VALIDATE_DAG_NAME,
                                      args),
        task_id=ARMADA_VALIDATE_DAG_NAME,
        dag=dag)

    armada_apply = SubDagOperator(
        subdag=get_armada_subdag_step(dag.dag_id,
                                      ARMADA_APPLY_DAG_NAME,
                                      args),
        task_id=ARMADA_APPLY_DAG_NAME,
        dag=dag)

    armada_get_releases = SubDagOperator(
        subdag=get_armada_subdag_step(dag.dag_id,
                                      ARMADA_GET_RELEASES_DAG_NAME,
                                      args),
        task_id=ARMADA_GET_RELEASES_DAG_NAME,
        dag=dag)

    # DAG Wiring
    armada_status.set_upstream(armada_client)
    armada_validate.set_upstream(armada_status)
    armada_apply.set_upstream(armada_validate)
    armada_get_releases.set_upstream(armada_apply)

    return dag
