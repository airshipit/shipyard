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
from airflow.operators import DryDockOperator
from airflow.operators import PromenadeOperator


# Location of shiyard.conf
# Note that the shipyard.conf file needs to be placed on a volume
# that can be accessed by the containers
config_path = '/usr/local/airflow/plugins/shipyard.conf'


def destroy_server(parent_dag_name, child_dag_name, args):
    '''
    Tear Down Node
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    # Drain Node
    promenade_drain_node = PromenadeOperator(
        task_id='promenade_drain_node',
        shipyard_conf=config_path,
        action='promenade_drain_node',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Remove Labels
    promenade_remove_labels = PromenadeOperator(
        task_id='promenade_remove_labels',
        shipyard_conf=config_path,
        action='promenade_remove_labels',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Stop Kubelet
    promenade_stop_kubelet = PromenadeOperator(
        task_id='promenade_stop_kubelet',
        shipyard_conf=config_path,
        action='promenade_stop_kubelet',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # ETCD Sanity Check
    promenade_check_etcd = PromenadeOperator(
        task_id='promenade_check_etcd',
        shipyard_conf=config_path,
        action='promenade_check_etcd',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Power down and destroy node using DryDock
    drydock_destroy_node = DryDockOperator(
        task_id='destroy_node',
        shipyard_conf=config_path,
        action='destroy_node',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Delete node from cluster using Promenade
    promenade_delete_node = PromenadeOperator(
        task_id='promenade_delete_node',
        shipyard_conf=config_path,
        action='promenade_delete_node',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Define dependencies
    promenade_remove_labels.set_upstream(promenade_drain_node)
    promenade_stop_kubelet.set_upstream(promenade_remove_labels)
    promenade_check_etcd.set_upstream(promenade_stop_kubelet)
    drydock_destroy_node.set_upstream(promenade_check_etcd)
    promenade_delete_node.set_upstream(drydock_destroy_node)

    return dag
