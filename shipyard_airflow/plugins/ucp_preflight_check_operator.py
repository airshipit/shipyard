# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
import os
import requests

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

from service_endpoint import ucp_service_endpoint


class UcpHealthCheckOperator(BaseOperator):
    """
    UCP Health Checks
    """

    @apply_defaults
    def __init__(self,
                 shipyard_conf,
                 *args,
                 **kwargs):

        super(UcpHealthCheckOperator, self).__init__(*args, **kwargs)
        self.shipyard_conf = shipyard_conf

    def execute(self, context):

        # Initialize variable
        # TODO: Include Promenade when its API endpoint is ready
        ucp_components = [
            'armada',
            'deckhand',
            'physicalprovisioner',
            'shipyard']

        # Loop through various UCP Components
        for i in ucp_components:

            # Define context 'svc_type'
            context['svc_type'] = i

            # Retrieve Endpoint Information
            context['svc_endpoint'] = ucp_service_endpoint(self, context)
            logging.info("%s endpoint is %s", i, context['svc_endpoint'])

            # Construct Health Check Endpoint
            healthcheck_endpoint = os.path.join(context['svc_endpoint'],
                                                'health')

            logging.info("%s healthcheck endpoint is %s", i,
                         healthcheck_endpoint)

            try:
                logging.info("Performing Health Check on %s", i)

                # Set health check timeout to 30 seconds
                req = requests.get(healthcheck_endpoint, timeout=30)
            except requests.exceptions.RequestException as e:
                raise AirflowException(e)

            # UCP Component will return empty response/body to show that
            # it is healthy
            if req.status_code == 204:
                logging.info("%s is alive and healthy", i)
            else:
                logging.error(req.text)
                raise AirflowException("Invalid Response!")


class UcpHealthCheckPlugin(AirflowPlugin):
    name = "ucp_healthcheck_plugin"
    operators = [UcpHealthCheckOperator]
