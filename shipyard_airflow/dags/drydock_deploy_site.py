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
from airflow.operators import DryDockOperator


# Location of shiyard.conf
# Note that the shipyard.conf file needs to be placed on a volume
# that can be accessed by the containers
config_path = '/usr/local/airflow/plugins/shipyard.conf'


def deploy_site_drydock(parent_dag_name, child_dag_name, args):
    '''
    DryDock Subdag
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    drydock_verify_site = DryDockOperator(
        task_id='verify_site',
        shipyard_conf=config_path,
        action='verify_site',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    drydock_prepare_site = DryDockOperator(
        task_id='prepare_site',
        shipyard_conf=config_path,
        action='prepare_site',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    drydock_prepare_nodes = DryDockOperator(
        task_id='prepare_nodes',
        shipyard_conf=config_path,
        action='prepare_nodes',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    drydock_deploy_nodes = DryDockOperator(
        task_id='deploy_nodes',
        shipyard_conf=config_path,
        action='deploy_nodes',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Define dependencies
    drydock_prepare_site.set_upstream(drydock_verify_site)
    drydock_prepare_nodes.set_upstream(drydock_prepare_site)
    drydock_deploy_nodes.set_upstream(drydock_prepare_nodes)

    return dag
