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
from airflow.operators import DeckhandOperator


# Location of shiyard.conf
# Note that the shipyard.conf file needs to be placed on a volume
# that can be accessed by the containers
config_path = '/usr/local/airflow/plugins/shipyard.conf'


def get_design_deckhand(parent_dag_name, child_dag_name, args):
    '''
    Get Deckhand Design Version
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    deckhand_design = DeckhandOperator(
        task_id='deckhand_get_design_version',
        shipyard_conf=config_path,
        action='deckhand_get_design_version',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    shipyard_retrieve_rendered_doc = DeckhandOperator(
        task_id='shipyard_retrieve_rendered_doc',
        shipyard_conf=config_path,
        action='shipyard_retrieve_rendered_doc',
        main_dag_name=parent_dag_name,
        sub_dag_name=child_dag_name,
        dag=dag)

    # Define dependencies
    shipyard_retrieve_rendered_doc.set_upstream(deckhand_design)

    return dag
