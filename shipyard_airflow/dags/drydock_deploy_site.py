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
from airflow.operators.subdag_operator import SubDagOperator
from airflow.operators import DryDockOperator


# Location of shiyard.conf
config_path = '/usr/local/airflow/plugins/shipyard.conf'

# Names used for sub-subdags in the drydock site deployment subdag
CREATE_DRYDOCK_CLIENT_DAG_NAME = 'create_drydock_client'
DRYDOCK_VERIFY_SITE_DAG_NAME = 'verify_site'
DRYDOCK_PREPARE_SITE_DAG_NAME = 'prepare_site'
DRYDOCK_PREPARE_NODE_DAG_NAME = 'prepare_node'
DRYDOCK_DEPLOY_NODE_DAG_NAME = 'deploy_node'


def get_drydock_subdag_step(parent_dag_name, child_dag_name, args):
    '''
    Execute DryDock Subdag
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)
    # Note that in the event where the 'deploy_site' action is
    # triggered from Shipyard, the 'parent_dag_name' variable
    # gets assigned with 'deploy_site.create_drydock_client'.
    # This is the name that we want to assign to the subdag so
    # that we can reference it for xcom. The name of the main
    # dag will be the front part of that value, i.e. 'deploy_site'.
    # Hence we will extract the front part and assign it to main_dag.
    # We will reuse this pattern for other Actions, e.g. update_site,
    # redeploy_site as well.
    operator = DryDockOperator(
        task_id=child_dag_name,
        shipyard_conf=config_path,
        action=child_dag_name,
        main_dag_name=parent_dag_name[0:parent_dag_name.find('.')],
        sub_dag_name=parent_dag_name,
        dag=dag)

    return dag


def deploy_site_drydock(parent_dag_name, child_dag_name, args):
    '''
    Puts all of the drydock deploy site into atomic unit
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    drydock_client = SubDagOperator(
        subdag=get_drydock_subdag_step(dag.dag_id,
                                       CREATE_DRYDOCK_CLIENT_DAG_NAME,
                                       args),
        task_id=CREATE_DRYDOCK_CLIENT_DAG_NAME,
        dag=dag)

    drydock_verify_site = SubDagOperator(
        subdag=get_drydock_subdag_step(dag.dag_id,
                                       DRYDOCK_VERIFY_SITE_DAG_NAME,
                                       args),
        task_id=DRYDOCK_VERIFY_SITE_DAG_NAME,
        dag=dag)

    drydock_prepare_site = SubDagOperator(
        subdag=get_drydock_subdag_step(dag.dag_id,
                                       DRYDOCK_PREPARE_SITE_DAG_NAME,
                                       args),
        task_id=DRYDOCK_PREPARE_SITE_DAG_NAME,
        dag=dag)

    drydock_prepare_node = SubDagOperator(
        subdag=get_drydock_subdag_step(dag.dag_id,
                                       DRYDOCK_PREPARE_NODE_DAG_NAME,
                                       args),
        task_id=DRYDOCK_PREPARE_NODE_DAG_NAME,
        dag=dag)

    drydock_deploy_node = SubDagOperator(
        subdag=get_drydock_subdag_step(dag.dag_id,
                                       DRYDOCK_DEPLOY_NODE_DAG_NAME,
                                       args),
        task_id=DRYDOCK_DEPLOY_NODE_DAG_NAME,
        dag=dag)

    # DAG Wiring
    drydock_verify_site.set_upstream(drydock_client)
    drydock_prepare_site.set_upstream(drydock_verify_site)
    drydock_prepare_node.set_upstream(drydock_prepare_site)
    drydock_deploy_node.set_upstream(drydock_prepare_node)

    return dag
