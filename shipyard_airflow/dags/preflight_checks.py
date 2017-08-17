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
from airflow.operators.subdag_operator import SubDagOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import PlaceholderOperator


def k8s_preflight_check(parent_dag_name, child_dag_name, args):
    '''
    The k8s_preflight_check checks that k8s is in a good state for
    the purposes of the Undercloud Platform to proceed with processing
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    # TODO () Replace this operator with a real operator that will:
    # 1) Ensure k8s is up and running.
    # 2) Ensure that pods are not crashed
    operator = PlaceholderOperator(task_id='k8s_preflight_check', dag=dag)

    return dag


def shipyard_preflight_check(parent_dag_name, child_dag_name, args):
    '''
    Checks that shipyard is in a good state for
    the purposes of the Undercloud Platform to proceed with processing
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    # TODO () Replace this operator with a real operator that will:
    # 1) Ensure shipyard is up and running.
    operator = PlaceholderOperator(task_id='shipyard_preflight_check', dag=dag)

    return dag


def deckhand_preflight_check(
        parent_dag_name,
        child_dag_name,
        args, ):
    '''
    Checks that deckhand is in a good state for
    the purposes of the Undercloud Platform to proceed with processing
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    # TODO () Replace this operator with a real operator that will:
    # 1) Ensure deckhand is up and running.
    operator = PlaceholderOperator(task_id='deckhand_preflight_check', dag=dag)

    return dag


def drydock_preflight_check(parent_dag_name, child_dag_name, args):
    '''
    Checks that drydock is in a good state for
    the purposes of the Undercloud Platform to proceed with processing
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    # TODO () Replace this operator with a real operator that will:
    # 1) Ensure drydock is up and running.
    operator = PlaceholderOperator(task_id='drydock_preflight_check', dag=dag)

    return dag


def armada_preflight_check(parent_dag_name, child_dag_name, args):
    '''
    Checks that armada is in a good state for
    the purposes of the Undercloud Platform to proceed with processing
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    # TODO () Replace this operator with a real operator that will:
    # 1) Ensure armada is up and running.
    operator = PlaceholderOperator(task_id='armada_preflight_check', dag=dag)

    return dag


# Names used for sub-subdags in the all preflight check subdag
K8S_PREFLIGHT_CHECK_DAG_NAME = 'k8s_preflight_check'
SHIPYARD_PREFLIGHT_CHECK_DAG_NAME = 'shipyard_preflight_check'
DECKHAND_PREFLIGHT_CHECK_DAG_NAME = 'deckhand_preflight_check'
DRYDOCK_PREFLIGHT_CHECK_DAG_NAME = 'drydock_preflight_check'
PROMENADE_PREFLIGHT_CHECK_DAG_NAME = 'promenade_preflight_check'
ARMADA_PREFLIGHT_CHECK_DAG_NAME = 'armada_preflight_check'


def all_preflight_checks(parent_dag_name, child_dag_name, args):
    '''
    puts all of the preflight checks into an atomic unit.
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    k8s = SubDagOperator(
        subdag=k8s_preflight_check(dag.dag_id, K8S_PREFLIGHT_CHECK_DAG_NAME,
                                   args),
        task_id=K8S_PREFLIGHT_CHECK_DAG_NAME,
        dag=dag, )

    shipyard = SubDagOperator(
        subdag=shipyard_preflight_check(
            dag.dag_id, SHIPYARD_PREFLIGHT_CHECK_DAG_NAME, args),
        task_id=SHIPYARD_PREFLIGHT_CHECK_DAG_NAME,
        dag=dag, )

    deckhand = SubDagOperator(
        subdag=deckhand_preflight_check(
            dag.dag_id, DECKHAND_PREFLIGHT_CHECK_DAG_NAME, args),
        task_id=DECKHAND_PREFLIGHT_CHECK_DAG_NAME,
        dag=dag, )

    drydock = SubDagOperator(
        subdag=drydock_preflight_check(dag.dag_id,
                                       DRYDOCK_PREFLIGHT_CHECK_DAG_NAME, args),
        task_id=DRYDOCK_PREFLIGHT_CHECK_DAG_NAME,
        dag=dag, )

    armada = SubDagOperator(
        subdag=armada_preflight_check(dag.dag_id,
                                      ARMADA_PREFLIGHT_CHECK_DAG_NAME, args),
        task_id=ARMADA_PREFLIGHT_CHECK_DAG_NAME,
        dag=dag, )

    return dag


def preflight_failure_handler(parent_dag_name, child_dag_name, args):
    '''
    Peforms the actions necessary when preflight checks fail
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DummyOperator(task_id='preflight_failure_handler', dag=dag)

    return dag
