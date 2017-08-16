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
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import DeckhandOperator
from airflow.operators import PlaceholderOperator


def validate_site_design_failure_handler(parent_dag_name, child_dag_name,
                                         args):
    '''
    Peforms the actions necessary when any of the site design checks fail
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DummyOperator(
        task_id='site_design_validation_failure_handler', dag=dag)

    return dag


def validate_site_design(parent_dag_name, child_dag_name, args):
    '''
    Subdag to delegate design verification to the UCP components
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    deckhand_validate_docs = DeckhandOperator(
        task_id='deckhand_validate_site_design', dag=dag)

    # TODO () use the real operator here
    drydock_validate_docs = PlaceholderOperator(
        task_id='drydock_validate_site_design', dag=dag)

    # TODO () use the real operator here
    armada_validate_docs = PlaceholderOperator(
        task_id='armada_validate_site_design', dag=dag)

    return dag
