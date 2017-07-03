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

import logging
import subprocess
import sys
import os

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

class TaskStateOperator(BaseOperator):
    """
    Retrieve Task State
    :airflow_dag_id: Dag ID
    :airflow_task_id: Task ID
    :airflow_execution_date: Task Execution Date
    """
    @apply_defaults
    def __init__(self,
                 airflow_command=None,
                 airflow_dag_id=None,
                 airflow_task_id=None,
                 airflow_execution_date=None,
                 *args, **kwargs):

        super(TaskStateOperator, self).__init__(*args, **kwargs)
        self.airflow_dag_id = airflow_dag_id
        self.airflow_task_id = airflow_task_id
        self.airflow_execution_date = airflow_execution_date
        self.airflow_command = ['airflow', 'task_state', airflow_dag_id, airflow_task_id, airflow_execution_date]

    def execute(self, context):
        logging.info("Running Airflow Command: %s", self.airflow_command)

        # Execute Airflow CLI Command
        airflow_cli = subprocess.Popen(self.airflow_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Logs Output
        # Filter out logging messages from standard output and keep only the relevant information
        line = ''
        for line in iter(airflow_cli.stdout.readline, b''):
            line = line.strip()

            if line.startswith( '[' ):
                pass
            else:
                logging.info(line)

        # Wait for child process to terminate. Set and return returncode attribute.
        airflow_cli.wait()

        # Raise Execptions if Task State Command Fails
        # Return XCOM State
        task_instance = context['task_instance']

        if airflow_cli.returncode:
            task_state = 'failed'
            task_instance.xcom_push('task_state', task_state)
            raise AirflowException("Failed to Retrieve Task State")
        else:
            task_state = line
            task_instance.xcom_push('task_state', task_state)


class TaskStatePlugin(AirflowPlugin):
    name = "task_state_plugin"
    operators = [TaskStateOperator]

