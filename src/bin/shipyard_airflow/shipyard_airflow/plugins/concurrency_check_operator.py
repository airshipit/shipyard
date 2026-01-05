# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
import logging
import requests
from urllib.parse import urljoin

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from oslo_config import cfg
from shipyard_airflow.plugins.xcom_pusher import XcomPusher

CONF = cfg.CONF

CONFLICTING_DAG_SETS = [
    set([
        'deploy_site', 'update_site', 'update_software', 'redeploy_server',
        'relabel_nodes'
    ])
]


def find_conflicting_dag_set(dag_name, conflicting_dag_sets=None):
    """
    Using dag_name, finds all other dag names that are in any set of
    conflicting dags from input conflicting_dag_sets
    """
    if conflicting_dag_sets is None:
        conflicting_dag_sets = CONFLICTING_DAG_SETS
    full_set = set()
    for single_set in conflicting_dag_sets:
        if dag_name in single_set:
            full_set = full_set | single_set
    full_set.discard(dag_name)
    logging.info('Potential conflicts: %s', ', '.join(full_set))
    return full_set


class ConcurrencyCheckOperator(BaseOperator):
    """
    Provides a way to indicate which DAGs should not be executing
    simultaneously using the Airflow API.
    """

    def __init__(self, conflicting_dag_set=None, *args, **kwargs):
        super(ConcurrencyCheckOperator, self).__init__(*args, **kwargs)
        self.conflicting_dag_set = conflicting_dag_set
        self.xcom_push = None

    def execute(self, context):
        """
        Run the check to see if this DAG has concurrency issues with other
        DAGs. Stop the workflow if there is.
        """
        self.xcom_push = XcomPusher(context['task_instance'])
        self._xcom_push_status(False)

        if self.conflicting_dag_set is None:
            self.check_dag_id = self.dag.dag_id
            logging.debug('dag_id is %s', self.check_dag_id)
            if '.' in self.dag.dag_id:
                self.check_dag_id = self.dag.dag_id.split('.', 1)[0]
                logging.debug('dag_id modified to %s', self.check_dag_id)

            logging.info('From dag %s, assuming %s for concurrency check',
                         self.dag.dag_id, self.check_dag_id)
            self.conflicting_dag_set = find_conflicting_dag_set(
                self.check_dag_id)

        logging.info('Checking for running of dags: %s',
                     ', '.join(self.conflicting_dag_set))

        conflicting_dag = self.find_conflicting_dag(self.check_dag_id)
        if conflicting_dag is None:
            logging.info('No conflicts found. Continuing Execution')
        else:
            self.abort_conflict(dag_name=self.check_dag_id,
                                conflict=conflicting_dag)
        self._xcom_push_status(True)

    def get_executing_dags(self):
        """
        Fetch the list of currently running DAGs using the Airflow API.
        Returns a list of tuples containing dag_id and logical_date.
        """
        web_server_url = CONF.base.web_server
        headers = {"Authorization": f"Bearer {self._get_airflow_api_token()}"}
        running_dags = []

        try:
            # Fetch all DAGs
            dags_url = urljoin(web_server_url, "/api/v2/dags?limit=10000")
            response = requests.get(dags_url, headers=headers, timeout=10)
            response.raise_for_status()
            dags = response.json()

            for dag in dags['dags']:
                dag_id = dag['dag_id']
                # Fetch DAG runs for each DAG
                dag_runs_url = urljoin(web_server_url,
                                       f"/api/v2/dags/{dag_id}"
                                       f"/dagRuns?limit=10000")
                dag_runs_response = requests.get(dag_runs_url,
                                                 headers=headers,
                                                 timeout=10)
                dag_runs_response.raise_for_status()
                dag_runs = dag_runs_response.json()

                # Filter running DAGs
                for dag_run in dag_runs['dag_runs']:
                    if dag_run['state'] == 'running':
                        running_dags.append((dag_id, dag_run['logical_date']))

        except requests.exceptions.RequestException as e:
            logging.error("Failed to fetch running DAGs from Airflow API: %s",
                          str(e))
            raise AirflowException(
                "Failed to fetch running DAGs from Airflow API")

        return running_dags

    def find_conflicting_dag(self, dag_id_to_check):
        """
        Checks for a DAG that is conflicting and exits based on the first
        one found. Also will return the dag_id_to_check as conflicting if
        more than 1 instance is running.
        """
        self_dag_count = 0
        for dag_id, execution_date in self.get_executing_dags():
            logging.info('Checking %s @ %s vs. current %s', dag_id,
                         execution_date, dag_id_to_check)
            if dag_id == dag_id_to_check:
                self_dag_count += 1
                logging.info(
                    "Found an instance of the dag_id being checked. Tally: %s",
                    self_dag_count)
            if dag_id in self.conflicting_dag_set:
                logging.info("Conflict found: %s @ %s", dag_id, execution_date)
                return dag_id
        if self_dag_count > 1:
            return dag_id_to_check
        return None

    def abort_conflict(self, dag_name, conflict):
        """
        Log and raise an exception that there is a conflicting workflow.
        """
        conflict_string = '{} conflicts with running {}. Aborting run'.format(
            dag_name, conflict)
        logging.error(conflict_string)
        raise AirflowException(conflict_string)

    def _xcom_push_status(self, status):
        """
        Push the status of the concurrency check.
        :param status: bool of whether or not this task is successful
        :return:
        """
        self.xcom_push.xcom_push(key="concurrency_check_success", value=status)

    def _get_airflow_api_token(self):
        """
        Fetch the Airflow API token (JWT) from the authentication endpoint.
        """
        token_url = urljoin(CONF.base.web_server, "auth/token")
        try:
            response = requests.get(token_url, timeout=10)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            logging.error("Failed to fetch Airflow API token: %s", str(e))
            raise AirflowException("Failed to fetch Airflow API token")


class ConcurrencyCheckPlugin(AirflowPlugin):
    """
    Register this plugin for this operator.
    """
    name = 'concurrency_check_operator_plugin'
    operators = [ConcurrencyCheckOperator]
