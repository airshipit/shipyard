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

import configparser

from airflow.models import DAG
from airflow.operators.subdag_operator import SubDagOperator
from airflow.operators import DryDockOperator


# Location of shiyard.conf
config_path = '/usr/local/airflow/plugins/shipyard.conf'

# Read and parse shiyard.conf
config = configparser.ConfigParser()
config.read(config_path)

# Define Variables
drydock_target_host = config.get('drydock', 'host')
drydock_port = config.get('drydock', 'port')
drydock_token = config.get('drydock', 'token')
drydock_conf = config.get('drydock', 'site_yaml')
promenade_conf = config.get('drydock', 'prom_yaml')
parent_dag = 'deploy_site'
child_dag = 'deploy_site.drydock_build'


def create_drydock_client(parent_dag_name, child_dag_name, args):
    '''
    Create Drydock Client
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='create_drydock_client',
        host=drydock_target_host,
        port=drydock_port,
        token=drydock_token,
        shipyard_conf=config_path,
        action='create_drydock_client',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def drydock_get_design_id(parent_dag_name, child_dag_name, args):
    '''
    Get Design ID
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='drydock_get_design_id',
        action='get_design_id',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def drydock_load_parts(parent_dag_name, child_dag_name, args):
    '''
    Load DryDock Yaml
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='drydock_load_parts',
        drydock_conf=drydock_conf,
        action='drydock_load_parts',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def promenade_load_parts(parent_dag_name, child_dag_name, args):
    '''
    Load Promenade Yaml
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='promenade_load_parts',
        promenade_conf=promenade_conf,
        action='promenade_load_parts',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def drydock_verify_site(parent_dag_name, child_dag_name, args):
    '''
    Verify connectivity between DryDock and MAAS
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='drydock_verify_site',
        action='verify_site',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def drydock_prepare_site(parent_dag_name, child_dag_name, args):
    '''
    Prepare site for deployment
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='drydock_prepare_site',
        action='prepare_site',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def drydock_prepare_node(parent_dag_name, child_dag_name, args):
    '''
    Prepare nodes for deployment
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='drydock_prepare_node',
        action='prepare_node',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


def drydock_deploy_node(parent_dag_name, child_dag_name, args):
    '''
    Deploy Nodes
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    operator = DryDockOperator(
        task_id='drydock_deploy_node',
        action='deploy_node',
        main_dag_name=parent_dag,
        sub_dag_name=child_dag,
        dag=dag)

    return dag


# Names used for sub-subdags in the drydock site deployment subdag
CREATE_DRYDOCK_CLIENT_DAG_NAME = 'create_drydock_client'
DRYDOCK_GET_DESIGN_ID_DAG_NAME = 'drydock_get_design_id'
DRYDOCK_LOAD_PARTS_DAG_NAME = 'drydock_load_parts'
PROMENADE_LOAD_PARTS_DAG_NAME = 'promenade_load_parts'
DRYDOCK_VERIFY_SITE_DAG_NAME = 'drydock_verify_site'
DRYDOCK_PREPARE_SITE_DAG_NAME = 'drydock_prepare_site'
DRYDOCK_PREPARE_NODE_DAG_NAME = 'drydock_prepare_node'
DRYDOCK_DEPLOY_NODE_DAG_NAME = 'drydock_deploy_node'


def deploy_site_drydock(parent_dag_name, child_dag_name, args):
    '''
    Puts all of the drydock deploy site into atomic unit
    '''
    dag = DAG(
        '{}.{}'.format(parent_dag_name, child_dag_name),
        default_args=args, )

    drydock_client = SubDagOperator(
        subdag=create_drydock_client(dag.dag_id,
                                     CREATE_DRYDOCK_CLIENT_DAG_NAME,
                                     args),
        task_id=CREATE_DRYDOCK_CLIENT_DAG_NAME,
        dag=dag, )

    design_id = SubDagOperator(
        subdag=drydock_get_design_id(
            dag.dag_id, DRYDOCK_GET_DESIGN_ID_DAG_NAME, args),
        task_id=DRYDOCK_GET_DESIGN_ID_DAG_NAME,
        dag=dag, )

    drydock_yaml = SubDagOperator(
        subdag=drydock_load_parts(
            dag.dag_id, DRYDOCK_LOAD_PARTS_DAG_NAME, args),
        task_id=DRYDOCK_LOAD_PARTS_DAG_NAME,
        dag=dag, )

    promenade_yaml = SubDagOperator(
        subdag=promenade_load_parts(dag.dag_id,
                                    PROMENADE_LOAD_PARTS_DAG_NAME, args),
        task_id=PROMENADE_LOAD_PARTS_DAG_NAME,
        dag=dag, )

    verify_site = SubDagOperator(
        subdag=drydock_verify_site(dag.dag_id,
                                   DRYDOCK_VERIFY_SITE_DAG_NAME, args),
        task_id=DRYDOCK_VERIFY_SITE_DAG_NAME,
        dag=dag, )

    prepare_site = SubDagOperator(
        subdag=drydock_prepare_site(dag.dag_id,
                                    DRYDOCK_PREPARE_SITE_DAG_NAME, args),
        task_id=DRYDOCK_PREPARE_SITE_DAG_NAME,
        dag=dag, )

    prepare_node = SubDagOperator(
        subdag=drydock_prepare_node(dag.dag_id,
                                    DRYDOCK_PREPARE_NODE_DAG_NAME, args),
        task_id=DRYDOCK_PREPARE_NODE_DAG_NAME,
        dag=dag, )

    deploy_node = SubDagOperator(
        subdag=drydock_deploy_node(dag.dag_id,
                                   DRYDOCK_DEPLOY_NODE_DAG_NAME, args),
        task_id=DRYDOCK_DEPLOY_NODE_DAG_NAME,
        dag=dag, )

    # DAG Wiring
    design_id.set_upstream(drydock_client)
    drydock_yaml.set_upstream(design_id)
    promenade_yaml.set_upstream(drydock_yaml)
    verify_site.set_upstream(promenade_yaml)
    prepare_site.set_upstream(verify_site)
    prepare_node.set_upstream(prepare_site)
    deploy_node.set_upstream(prepare_node)

    return dag
