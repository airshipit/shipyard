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
    from airflow.operators import DrydockDestroyNodeOperator
    from airflow.operators import PromenadeCheckEtcdOperator
    from airflow.operators import PromenadeClearLabelsOperator
    from airflow.operators import PromenadeDecommissionNodeOperator
    from airflow.operators import PromenadeDrainNodeOperator
    from airflow.operators import PromenadeShutdownKubeletOperator
    from config_path import config_path
except ImportError:
    from shipyard_airflow.plugins.drydock_destroy_nodes import \
        DrydockDestroyNodeOperator
    from shipyard_airflow.plugins.promenade_check_etcd import \
        PromenadeCheckEtcdOperator
    from shipyard_airflow.plugins.promenade_clear_labels import \
        PromenadeClearLabelsOperator
    from shipyard_airflow.plugins.promenade_decommission_node import \
        PromenadeDecommissionNodeOperator
    from shipyard_airflow.plugins.promenade_drain_node import \
        PromenadeDrainNodeOperator
    from shipyard_airflow.plugins.promenade_shutdown_kubelet import \
        PromenadeShutdownKubeletOperator
    from shipyard_airflow.dags.config_path import config_path


def destroy_server(dag):
    """DAG to tear down node

    The DAG will make use of the promenade and drydock operators
    to tear down a target node.

    """
    with TaskGroup(group_id="destroy_server", dag=dag) as destroy_server:

        # Drain Node
        promenade_drain_node = PromenadeDrainNodeOperator(
            task_id='promenade_drain_node',
            shipyard_conf=config_path,
            dag=dag)

        # Clear Labels
        promenade_clear_labels = PromenadeClearLabelsOperator(
            task_id='promenade_clear_labels',
            shipyard_conf=config_path,
            dag=dag)

        # Shutdown Kubelet
        promenade_shutdown_kubelet = PromenadeShutdownKubeletOperator(
            task_id='promenade_shutdown_kubelet',
            shipyard_conf=config_path,
            dag=dag)

        # ETCD Sanity Check
        promenade_check_etcd = PromenadeCheckEtcdOperator(
            task_id='promenade_check_etcd',
            shipyard_conf=config_path,
            dag=dag)

        # Power down and destroy node using DryDock
        drydock_destroy_node = DrydockDestroyNodeOperator(
            task_id='destroy_node',
            shipyard_conf=config_path,
            dag=dag)

        # Decommission node from Kubernetes cluster using Promenade
        promenade_decommission_node = PromenadeDecommissionNodeOperator(
            task_id='promenade_decommission_node',
            shipyard_conf=config_path,
            dag=dag)

        # Define dependencies
        promenade_clear_labels.set_upstream(promenade_drain_node)
        promenade_shutdown_kubelet.set_upstream(promenade_clear_labels)
        promenade_check_etcd.set_upstream(promenade_shutdown_kubelet)
        drydock_destroy_node.set_upstream(promenade_check_etcd)
        promenade_decommission_node.set_upstream(drydock_destroy_node)

        return destroy_server
