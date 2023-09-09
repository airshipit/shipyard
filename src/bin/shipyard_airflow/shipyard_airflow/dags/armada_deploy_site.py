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
    from airflow.operators import ArmadaGetReleasesOperator
    from airflow.operators import ArmadaPostApplyOperator
    from config_path import config_path
except ImportError:
    from shipyard_airflow.plugins.armada_get_releases import \
        ArmadaGetReleasesOperator
    from shipyard_airflow.plugins.armada_post_apply import \
        ArmadaPostApplyOperator
    from shipyard_airflow.dags.config_path import config_path


def deploy_site_armada(dag):
    '''
    Armada TaskGroup
    '''
    with TaskGroup(group_id="armada_build", dag=dag) as armada_build:
        """Generate the armada post_apply step

        Armada post_apply does the deployment of helm charts
        """
        armada_post_apply = ArmadaPostApplyOperator(
            task_id='armada_post_apply',
            shipyard_conf=config_path,
            retries=5,
            dag=dag)
        """Generate the armada get_releases step

        Armada get_releases does the verification of releases of helm charts
        """
        armada_get_releases = ArmadaGetReleasesOperator(
            task_id='armada_get_releases',
            shipyard_conf=config_path,
            dag=dag)

        armada_post_apply >> armada_get_releases

        return armada_build
