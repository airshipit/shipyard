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
from airflow.operators.subdag_operator import SubDagOperator


# Location of shiyard.conf
config_path = '/usr/local/airflow/plugins/shipyard.conf'

# Define Variables
parent_dag = 'deploy_site'
child_dag = 'deploy_site.deckhand_get_design_version'

# Names used for sub-subdags in the deckhand subdag
DECKHAND_GET_DESIGN_VERSION_DAG_NAME = 'deckhand_get_design_version'


def get_design_version(parent_dag_name, child_dag_name, args):
    '''
    Get Deckhand Design Version
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    operator = DeckhandOperator(
        task_id=DECKHAND_GET_DESIGN_VERSION_DAG_NAME,
        shipyard_conf=config_path,
        action=DECKHAND_GET_DESIGN_VERSION_DAG_NAME,
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def get_design_deckhand(parent_dag_name, child_dag_name, args):
    '''
    Puts into atomic unit
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    deckhand_design = SubDagOperator(
        subdag=get_design_version(dag.dag_id,
                                  DECKHAND_GET_DESIGN_VERSION_DAG_NAME,
                                  args),
        task_id=DECKHAND_GET_DESIGN_VERSION_DAG_NAME,
        dag=dag)

    return dag
