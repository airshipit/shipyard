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
from airflow.operators import K8sHealthCheckOperator
from airflow.operators import UcpHealthCheckOperator


# Location of shiyard.conf
# Note that the shipyard.conf file needs to be placed on a volume
# that can be accessed by the containers
config_path = '/usr/local/airflow/plugins/shipyard.conf'


# TODO: Add Checks for Promenade when the API is ready
def all_preflight_checks(parent_dag_name, child_dag_name, args):
    '''
    Pre-Flight Checks Subdag
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    '''
    The k8s_preflight_check checks that k8s is in a good state
    for the purposes of the Undercloud Platform to proceed with
    processing
    '''
    k8s = K8sHealthCheckOperator(
        task_id='k8s_preflight_check',
        dag=dag)

    '''
    Checks that shipyard is in a good state for the purposes of the
    Undercloud Platform to proceed with processing
    '''
    shipyard = UcpHealthCheckOperator(
        task_id='shipyard_preflight_check',
        shipyard_conf=config_path,
        ucp_node='shipyard',
        dag=dag)

    '''
    Checks that deckhand is in a good state for the purposes of the
    Undercloud Platform to proceed with processing
    '''
    deckhand = UcpHealthCheckOperator(
        task_id='deckhand_preflight_check',
        shipyard_conf=config_path,
        ucp_node='deckhand',
        dag=dag)

    '''
    Checks that drydock is in a good state for the purposes of the
    Undercloud Platform to proceed with processing
    '''
    drydock = UcpHealthCheckOperator(
        task_id='drydock_preflight_check',
        shipyard_conf=config_path,
        ucp_node='drydock',
        dag=dag)

    '''
    Checks that armada is in a good state for the purposes of the
    Undercloud Platform to proceed with processing
    '''
    armada = UcpHealthCheckOperator(
        task_id='armada_preflight_check',
        shipyard_conf=config_path,
        ucp_node='armada',
        dag=dag)

    return dag
