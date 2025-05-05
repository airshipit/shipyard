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

from airflow.utils.task_group import TaskGroup

try:
    from airflow.operators import DrydockNodesOperator
    from airflow.operators import DrydockPrepareSiteOperator
    from airflow.operators import DrydockVerifySiteOperator
    from airflow.operators import DrydockVerifyNodesExistOperator
    from config_path import config_path
except ImportError:
    from shipyard_airflow.plugins.drydock_nodes import \
        DrydockNodesOperator
    from shipyard_airflow.plugins.drydock_prepare_site import \
        DrydockPrepareSiteOperator
    from shipyard_airflow.plugins.drydock_verify_site import \
        DrydockVerifySiteOperator
    from shipyard_airflow.plugins.drydock_verify_nodes import \
        DrydockVerifyNodesExistOperator
    from shipyard_airflow.dags.config_path import config_path


def deploy_site_drydock(dag, verify_nodes_exist=False):
    '''
    DryDock TaskGroup
    '''
    with TaskGroup(group_id="drydock_build", dag=dag) as drydock_build:

        if verify_nodes_exist:
            drydock_verify_nodes_exist = DrydockVerifyNodesExistOperator(
                task_id='verify_nodes_exist',
                main_dag_name=dag.dag_id.split('.')[0],
                shipyard_conf=config_path,
                dag=dag
            )

        drydock_verify_site = DrydockVerifySiteOperator(
            task_id='verify_site',
            main_dag_name=dag.dag_id.split('.')[0],
            shipyard_conf=config_path,
            dag=dag
        )

        drydock_prepare_site = DrydockPrepareSiteOperator(
            task_id='prepare_site',
            main_dag_name=dag.dag_id.split('.')[0],
            shipyard_conf=config_path,
            dag=dag
        )

        drydock_nodes = DrydockNodesOperator(
            task_id='prepare_and_deploy_nodes',
            main_dag_name=dag.dag_id.split('.')[0],
            shipyard_conf=config_path,
            dag=dag
        )

        # Define dependencies
        drydock_prepare_site.set_upstream(drydock_verify_site)
        if verify_nodes_exist:
            drydock_verify_nodes_exist.set_upstream(drydock_prepare_site)
            drydock_nodes.set_upstream(drydock_verify_nodes_exist)
        else:
            drydock_nodes.set_upstream(drydock_prepare_site)

        return drydock_build
