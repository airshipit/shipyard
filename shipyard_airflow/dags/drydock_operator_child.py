# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
### DryDock Operator Child Dag
"""
import airflow
import configparser
from airflow import DAG
from airflow.operators import DryDockOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


def sub_dag(parent_dag_name, child_dag_name, args, schedule_interval):
  dag = DAG(
    '%s.%s' % (parent_dag_name, child_dag_name),
    default_args=args,
    start_date=args['start_date'],
    max_active_runs=1,
  )

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

  # Convert to Dictionary
  k8_masters_sting = config.get('drydock', 'k8_masters')
  k8_masters_list = k8_masters_sting.split(',')
  k8_masters = {'node_names': k8_masters_list}

  # Create Drydock Client
  t1 = DryDockOperator(
      task_id='create_drydock_client',
      host=drydock_target_host,
      port=drydock_port,
      token=drydock_token,
      shipyard_conf=config_path,
      action='create_drydock_client',
      dag=dag)

  # Get Design ID
  t2 = DryDockOperator(
      task_id='drydock_get_design_id',
      action='get_design_id',
      dag=dag)

  # DryDock Load Parts
  t3 = DryDockOperator(
      task_id='drydock_load_parts',
      drydock_conf=drydock_conf,
      action='drydock_load_parts',
      dag=dag)

  # Promenade Load Parts
  t4 = DryDockOperator(
      task_id='promenade_load_parts',
      promenade_conf=promenade_conf,
      action='promenade_load_parts',
      dag=dag)

  # Verify Site
  t5 = DryDockOperator(
      task_id='drydock_verify_site',
      action='verify_site',
      dag=dag)

  # Prepare Site
  t6 = DryDockOperator(
      task_id='drydock_prepare_site',
      action='prepare_site',
      dag=dag)

  # Prepare Node
  t7 = DryDockOperator(
      task_id='drydock_prepare_node',
      action='prepare_node',
      node_filter=k8_masters,
      dag=dag)

  # Deploy Node
  t8 = DryDockOperator(
      task_id='drydock_deploy_node',
      action='deploy_node',
      node_filter=k8_masters,
      dag=dag)

  # Define dependencies
  t2.set_upstream(t1)
  t3.set_upstream(t2)
  t4.set_upstream(t3)
  t5.set_upstream(t4)
  t6.set_upstream(t5)
  t7.set_upstream(t6)
  t8.set_upstream(t7)

  return dag
