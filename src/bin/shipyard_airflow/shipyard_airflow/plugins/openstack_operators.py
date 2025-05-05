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
import os
import configparser

from airflow.exceptions import AirflowException
from airflow.sdk import BaseOperator
from airflow.plugins_manager import AirflowPlugin


class OpenStackOperator(BaseOperator):
    """
    Performs OpenStack CLI calls
    :shipyard_conf: Location of shipyard.conf
    :openstack_command: The OpenStack command to be executed
    """

    def __init__(self,
                 shipyard_conf,
                 openstack_command=None,
                 xcom_push=False,
                 *args,
                 **kwargs):

        super(OpenStackOperator, self).__init__(*args, **kwargs)
        self.shipyard_conf = shipyard_conf
        self.openstack_command = openstack_command
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        logging.info("Running OpenStack Command: %s", self.openstack_command)

        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        # Construct Envrionment Variables
        for attr in ('OS_AUTH_URL', 'OS_PROJECT_NAME', 'OS_USER_DOMAIN_NAME',
                     'OS_USERNAME', 'OS_PASSWORD', 'OS_REGION_NAME',
                     'OS_IDENTITY_API_VERSION'):
            os.environ[attr] = config.get('keystone', attr)

        # Execute the OpenStack CLI Command
        openstack_cli = subprocess.Popen(  # nosec
            self.openstack_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        # Logs Output
        logging.info("Output:")

        line = ''
        for line in iter(openstack_cli.stdout.readline, b''):
            line = line.strip()
            logging.info(line)

        # Wait for child process to terminate
        # Set and return returncode attribute.
        openstack_cli.wait()
        logging.info("Command exited with "
                     "return code {0}".format(openstack_cli.returncode))

        # Raise Execptions if OpenStack Command Fails
        if openstack_cli.returncode:
            raise AirflowException("OpenStack Command Failed")


class OpenStackCliPlugin(AirflowPlugin):
    name = "openstack_cli_plugin"
    operators = [OpenStackOperator]
