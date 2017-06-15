"""
OpenStack CLI

Perform basic OpenStack CLI calls
"""
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2017, 6, 14),
    'email': ['airflow@airflow.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG('openstack_api_call', default_args=default_args, schedule_interval=None)

# print_date
t1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag)

# Current assumption is that we will be able to retrieve information from
# data manager (DeckHand) to create the admin-openrc.sh that is needed for
# airflow to perform OpenStack API calls
t2 = BashOperator(
    task_id='nova_list',
    bash_command='source ' + os.getcwd() + '/dags/admin-openrc.sh' + ';' + 'nova' + ' list',
    retries=3,
    dag=dag)

t3 = BashOperator(
    task_id='neutron_net_list',
    bash_command='source ' + os.getcwd() + '/dags/admin-openrc.sh' + ';' + 'neutron' + ' net-list',
    retries=3,
    dag=dag)

t2.set_upstream(t1)
t3.set_upstream(t1)

