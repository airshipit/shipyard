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
from airflow.sdk import BaseOperator
from airflow.plugins_manager import AirflowPlugin

try:
    import service_endpoint
    from xcom_puller import XcomPuller
    from xcom_pusher import XcomPusher
except ImportError:
    from shipyard_airflow.plugins import service_endpoint
    from shipyard_airflow.plugins.xcom_puller import XcomPuller
    from shipyard_airflow.plugins.xcom_pusher import XcomPusher

LOG = logging.getLogger(__name__)


class UcpHealthCheckOperator(BaseOperator):
    """
    Airship Health Checks
    """

    def __init__(self,
                 shipyard_conf=None,
                 main_dag_name=None,
                 xcom_push=True,
                 *args,
                 **kwargs):

        super(UcpHealthCheckOperator, self).__init__(*args, **kwargs)
        self.shipyard_conf = shipyard_conf
        self.main_dag_name = main_dag_name
        self.xcom_push_flag = xcom_push
        self.endpoints = service_endpoint.ServiceEndpoints(self.shipyard_conf)

    def execute(self, context):

        # Initialize variable
        ucp_components = [
            service_endpoint.ARMADA, service_endpoint.DECKHAND,
            service_endpoint.DRYDOCK, service_endpoint.PROMENADE,
            service_endpoint.SHIPYARD
        ]

        # Define task_instance
        self.task_instance = context['task_instance']

        # Set up and retrieve values from xcom
        self.xcom_puller = XcomPuller(self.main_dag_name, self.task_instance)
        self.action_info = self.xcom_puller.get_action_info()

        # Set up xcom_pusher to push values to xcom
        self.xcom_pusher = XcomPusher(self.task_instance)

        # Loop through various Airship Components
        for component in ucp_components:

            # Retrieve Endpoint Information
            endpoint = self.endpoints.endpoint_by_name(component)
            LOG.info("%s endpoint is %s", component, endpoint)

            # Construct Health Check Endpoint
            healthcheck_endpoint = os.path.join(endpoint, 'health')

            try:
                LOG.info("Performing Health Check on %s at %s", component,
                         healthcheck_endpoint)
                # Set health check timeout to 30 seconds
                req = requests.get(healthcheck_endpoint, timeout=30)

                # An empty response/body returned by a component means
                # that it is healthy
                if req.status_code == 204:
                    LOG.info("%s is alive and healthy", component)

            except requests.exceptions.RequestException as e:
                self.log_health_exception(component, e)

    def log_health_exception(self, component, error_messages):
        """Logs Exceptions for health check
        """
        # If Drydock health check fails and continue-on-fail, continue
        # and create xcom key 'drydock_continue_on_fail'
        # Note that 'update_software' does not interact with Drydock, and
        # therefore does not use the continue-on-fail option.
        if (component == service_endpoint.DRYDOCK and
                self.action_info['parameters'].get(
                    'continue-on-fail', 'false').lower() == 'true' and
                self.action_info['dag_id'] in ['update_site', 'deploy_site']):
            LOG.warning('Drydock did not pass health check. Continuing '
                        'as "continue-on-fail" option is enabled.')
            self.xcom_pusher.xcom_push(key='drydock_continue_on_fail',
                                       value=True)

        else:
            LOG.error(error_messages)
            raise AirflowException(
                "Health check failed for %s component on "
                "dag_id=%s. Details: %s" %
                (component, self.action_info.get('dag_id'), error_messages))


class UcpHealthCheckPlugin(AirflowPlugin):
    name = "ucp_healthcheck_plugin"
    operators = [UcpHealthCheckOperator]
