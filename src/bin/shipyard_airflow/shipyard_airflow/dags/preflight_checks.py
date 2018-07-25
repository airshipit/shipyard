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

try:
    from airflow.operators import UcpHealthCheckOperator
    from config_path import config_path
except ImportError:
    from shipyard_airflow.plugins.ucp_preflight_check_operator import \
        UcpHealthCheckOperator
    from shipyard_airflow.dags.config_path import config_path


def all_preflight_checks(parent_dag_name, child_dag_name, args):
    '''
    Pre-Flight Checks Subdag
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    '''
    Check that all UCP components are in good state for the purposes
    of the Undercloud Platform to proceed with processing.
    '''
    shipyard = UcpHealthCheckOperator(
        task_id='ucp_preflight_check',
        shipyard_conf=config_path,
        main_dag_name=parent_dag_name,
        dag=dag)

    return dag
