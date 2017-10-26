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
import configparser

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from socket import timeout


class UcpHealthCheckOperator(BaseOperator):
    """
    UCP Health Checks
    :shipyard_conf: Location of shipyard.conf
    :ucp_node: ucp node to perform health check on
    """

    @apply_defaults
    def __init__(self,
                 shipyard_conf,
                 ucp_node,
                 *args,
                 **kwargs):

        super(UcpHealthCheckOperator, self).__init__(*args, **kwargs)
        self.shipyard_conf = shipyard_conf
        self.ucp_node = ucp_node

    def execute(self, context):
        logging.info("Performing Health Check on %s", self.ucp_node)

        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        # Construct Health Check API Endpoint
        schema = config.get('healthcheck', 'schema')
        endpoint = config.get('healthcheck', 'endpoint')
        host = config.get(self.ucp_node, 'host')
        port = config.get(self.ucp_node, 'port')

        url = schema + '://' + host + ':' + port + endpoint

        try:
            # Set health check timeout to 30 seconds
            # using nosec since the urls are taken from our own configuration
            # files only, never external.
            req = urlopen(url, timeout=30).read().decode('utf-8')  # nosec
        except (HTTPError, URLError) as error:
            # Raise Exception for HTTP/URL Error
            logging.error('Error Encountered: %s', error)
            raise AirflowException("HTTP/URL Error Encountered")
        except timeout:
            # Raise Exception for Timeout
            logging.error('Health Check Timed Out for %s', self.ucp_node)
            raise AirflowException("Health Check Timed Out")
        else:
            logging.info("%s is alive and healthy", self.ucp_node)


class UcpHealthCheckPlugin(AirflowPlugin):
    name = "ucp_healthcheck_plugin"
    operators = [UcpHealthCheckOperator]
