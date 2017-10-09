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
from airflow.operators import PlaceholderOperator
from airflow.operators.subdag_operator import SubDagOperator


'''
Note that in the event where the 'deploy_site' Action is triggered
from Shipyard, the 'parent_dag_name' variable gets assigned with
'deploy_site.validate_site_design'. The name of the main dag will
be the front part of that value, i.e. 'deploy_site'. Hence we will
extract the front part and assign it to main_dag for the functions
defined below
'''
# Location of shiyard.conf
config_path = '/usr/local/airflow/plugins/shipyard.conf'

# Names used for sub-subdags in UCP components design verification
DECKHAND_VALIDATE_DOCS_DAG_NAME = 'deckhand_validate_site_design'


def deckhand_validate_site_design(parent_dag_name, child_dag_name, args):
    '''
    Validate Site Design - Deckhand
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    # Assigns value 'deploy_site.deckhand_validate_site_design' to
    # the sub_dag
    child_dag = parent_dag_name[0:parent_dag_name.find('.')] + \
        '.' + DECKHAND_VALIDATE_DOCS_DAG_NAME

    operator = DeckhandOperator(
        task_id=DECKHAND_VALIDATE_DOCS_DAG_NAME,
        shipyard_conf=config_path,
        action=DECKHAND_VALIDATE_DOCS_DAG_NAME,
        main_dag_name=parent_dag_name[0:parent_dag_name.find('.')],
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def validate_site_design(parent_dag_name, child_dag_name, args):
    '''
    Subdag to delegate design verification to the UCP components
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args)

    deckhand_validate_docs = SubDagOperator(
        subdag=deckhand_validate_site_design(dag.dag_id,
                                             DECKHAND_VALIDATE_DOCS_DAG_NAME,
                                             args),
        task_id=DECKHAND_VALIDATE_DOCS_DAG_NAME,
        dag=dag)

    # TODO () use the real operator here
    drydock_validate_docs = PlaceholderOperator(
        task_id='drydock_validate_site_design', dag=dag)

    # TODO () use the real operator here
    armada_validate_docs = PlaceholderOperator(
        task_id='armada_validate_site_design', dag=dag)

    return dag
