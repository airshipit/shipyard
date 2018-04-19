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
from airflow.operators import DeploymentConfigurationOperator

from config_path import config_path


GET_DEPLOYMENT_CONFIGURATION_NAME = 'get_deployment_configuration'


def get_deployment_configuration(parent_dag_name, child_dag_name, args):
    """DAG to retrieve deployment configuration"""
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    deployment_configuration = DeploymentConfigurationOperator(
        task_id=GET_DEPLOYMENT_CONFIGURATION_NAME,
        shipyard_conf=config_path,
        main_dag_name=parent_dag_name,
        dag=dag)

    return dag
