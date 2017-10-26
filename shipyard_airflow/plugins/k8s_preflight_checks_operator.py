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
# Using nosec to prevent Bandit blacklist reporting. Subprocess is used
# in a controlled way as part of this operator.
import subprocess  # nosec

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults


class K8sHealthCheckOperator(BaseOperator):
    """
    Performs basic Kubernetes Health Check
    """
    @apply_defaults
    def __init__(self,
                 *args, **kwargs):

        super(K8sHealthCheckOperator, self).__init__(*args, **kwargs)

    def execute(self, context):
        logging.info("Running Basic Kubernetes Cluster Health Check:")

        # Location of Token
        token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'

        # Read content of token file as string
        with open(token_path, "r") as token_file:
            token = token_file.read()

        # Location of CA Certificate
        ca = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'

        # The current health checks only check to ensure that all
        # pods are in 'running' state.  The k8s health checks can
        # be expanded in future if need be.
        k8s_command = [
            'kubectl', '--token', token,
            '--certificate-authority', ca,
            'get', 'pods', '--all-namespaces']

        # Execute the Kubernetes Health Check Command
        k8s_output = subprocess.Popen(  # nosec
            k8s_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        # Logs Output
        logging.info("Output:")

        line = ''
        for line in iter(k8s_output.stdout.readline, b''):
            line = line.strip()
            logging.info(line)
            # Skip the first line of output
            if 'STATUS' in str(line, 'utf-8'):
                continue
            # Do nothing if pod is in 'Running' state
            elif str(line, 'utf-8').split()[3] == 'Running':
                continue
            # Raise Exceptions if Pod is in state other than
            # 'Running'
            else:
                pod = str(line, 'utf-8').split()[0]
                pod_state = str(line, 'utf-8').split()[3]
                logging.error('Pod %s is in %s state', pod, pod_state)
                raise AirflowException("Kubernetes Health Checks Failed!")

        # Wait for child process to terminate
        # Set and return returncode attribute.
        k8s_output.wait()
        logging.info("Command exited with "
                     "return code {0}".format(k8s_output.returncode))

        # Raise Execptions if Kubernetes Command Fails
        if k8s_output.returncode:
            raise AirflowException("Kubernetes Command Failed")


class K8sHealthCheckPlugin(AirflowPlugin):
    name = "k8s_healthcheck_plugin"
    operators = [K8sHealthCheckOperator]
