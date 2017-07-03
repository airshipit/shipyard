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

class OpenStackOperator(BaseOperator):
    """
    Performs OpenStack CLI calls
    :openrc_file: Path of the openrc file
    :openstack_command: The OpenStack command to be executed
    """
    @apply_defaults
    def __init__(self,
                 openrc_file,
                 openstack_command=None,
                 xcom_push=False,
                 *args, **kwargs):

        super(OpenStackOperator, self).__init__(*args, **kwargs)
        self.openrc_file = openrc_file
        self.openstack_command = openstack_command
        self.xcom_push_flag = xcom_push

    def execute(self, context):
        logging.info("Running OpenStack Command: " + ' '.join(self.openstack_command))

        # Build environment variables.
        pipe = subprocess.Popen(". %s; env" % self.openrc_file, stdout=subprocess.PIPE, shell=True)
        data = pipe.communicate()[0]
        os_env = dict((line.split("=", 1) for line in data.splitlines()))

        # Execute the OpenStack CLI Command
        openstack_cli = subprocess.Popen(self.openstack_command, env=os_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Logs Output
        logging.info("Output:")

        line = ''
        for line in iter(openstack_cli.stdout.readline, b''):
            line = line.strip()
            logging.info(line)

        # Wait for child process to terminate. Set and return returncode attribute.
        openstack_cli.wait()
        logging.info("Command exited with "
                     "return code {0}".format(openstack_cli.returncode))

        # Raise Execptions if OpenStack Command Fails
        if openstack_cli.returncode:
            raise AirflowException("OpenStack Command Failed")


        """
        Push response to an XCom if xcom_push is True
        """
        if self.xcom_push_flag:
            return line


class OpenStackCliPlugin(AirflowPlugin):
    name = "openstack_cli_plugin"
    operators = [OpenStackOperator]

