# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
import falcon
import logging
import os
import requests

from oslo_config import cfg

from shipyard_airflow import policy
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.control.helpers.action_helper import ActionsHelper

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ActionsStepsLogsResource(BaseResource):
    """
    The actions steps logs resource retrieves the logs for a particular
    step of an action. By default, it will retrieve the logs from the
    last attempt. Note that a workflow step can retry multiple times with
    the names of the logs as 1.log, 2.log, 3.log, etc.

    """
    @policy.ApiEnforcer(policy.GET_ACTION_STEP_LOGS)
    def on_get(self, req, resp, **kwargs):
        """
        Returns the logs of an action step
        :returns: logs of an action step
        """
        # We will set the kwarg to 'try_number' as 'try' is a
        # reserved keyword
        try_number = req.get_param_as_int('try',
                                          required=False)

        # Parse kwargs
        action_id = ActionsHelper.parse_action_id(**kwargs)
        step_id = ActionsHelper.parse_step_id(**kwargs)

        # Retrieve logs for the action step
        resp.body = self.get_action_step_logs(action_id,
                                              step_id,
                                              try_number)

        resp.status = falcon.HTTP_200

    def get_action_step_logs(self, action_id, step_id, try_number=None):
        """
        Retrieve Airflow Logs
        """
        # Set up actions helper
        self.actions_helper = ActionsHelper(action_id=action_id)

        # Retrieve step
        step = self.actions_helper.get_step(step_id, try_number)

        # Retrieve Dag ID
        dag_id = step['dag_id']

        # Generate Log Endpoint
        log_endpoint = self.generate_log_endpoint(step,
                                                  dag_id,
                                                  step_id,
                                                  try_number)

        LOG.debug("Log endpoint url is: %s", log_endpoint)

        return self.retrieve_logs(log_endpoint)

    def generate_log_endpoint(self, step, dag_id, step_id, try_number):
        """
        Retrieve Log Endpoint
        """
        # Construct worker pod URL
        scheme = CONF.airflow.worker_endpoint_scheme
        worker_pod_fqdn = step['hostname']
        worker_pod_port = CONF.airflow.worker_port
        worker_pod_url = "{}://{}:{}".format(scheme,
                                             worker_pod_fqdn,
                                             str(worker_pod_port))

        # Define log_file
        if try_number:
            log_file = str(try_number) + '.log'
        else:
            log_file = str(step['try_number']) + '.log'

        # Define dag_execution_date
        dag_execution_date = (
            self.actions_helper.get_formatted_dag_execution_date(step))

        # Form logs query endpoint
        log_endpoint = os.path.join(worker_pod_url,
                                    'log',
                                    dag_id,
                                    step_id,
                                    dag_execution_date,
                                    log_file)

        return log_endpoint

    @staticmethod
    def retrieve_logs(log_endpoint):
        """
        Retrieve Logs
        """
        try:
            LOG.debug("Retrieving Airflow logs...")

            response = requests.get(
                log_endpoint,
                timeout=(
                    CONF.requests_config.airflow_log_connect_timeout,
                    CONF.requests_config.airflow_log_read_timeout))

            return response.text

        except requests.exceptions.RequestException as e:
            LOG.info(e)
            LOG.info("Unable to retrieve requested logs")
            return []
