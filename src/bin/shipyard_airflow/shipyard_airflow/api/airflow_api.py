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
import os
import pytz
import requests
import falcon
import logging
import pendulum

from oslo_config import cfg
from shipyard_airflow.errors import ApiError
from shipyard_airflow.api.errors import AirflowStateError

from requests.exceptions import RequestException

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class AirflowApiAccess:
    """
    Encapsulates access to Airflow API v2.
    Provides methods for retrieving DAG runs, task instances, etc.
    """

    def __init__(self):
        self.web_server_url = CONF.base.web_server
        self.c_timeout = CONF.base.airflow_api_connect_timeout
        self.r_timeout = CONF.base.airflow_api_read_timeout

    def _get_token(self):
        token_url = os.path.join(
            self.web_server_url, 'auth/token')
        resp = requests.get(
            token_url, timeout=(self.c_timeout, self.r_timeout))
        resp.raise_for_status()
        token = resp.json().get('access_token')
        if not token:
            raise ApiError(
                title='Unable to retrieve JWT token',
                description='Airflow did not return a valid access token.',
                status=503,
                retry=True,
            )
        return token

    def _get_headers(self):
        token = self._get_token()
        return {
            'Cache-Control': 'no-cache',
            'Authorization': f'Bearer {token}'
        }

    def get_dag_list(self):
        """
        Retrieves the list of all DAGs using the Airflow v2 REST API.
        Returns a list of dictionaries representing DAGs.
        """
        web_server_url = self.web_server_url
        headers = self._get_headers()

        dag_list_url = os.path.join(web_server_url, 'api/v2/dags?limit=10000')
        LOG.info("Requesting DAG list from URL: %s", dag_list_url)
        resp = requests.get(
            dag_list_url,
            timeout=(self.c_timeout, self.r_timeout),
            headers=headers
        )
        LOG.debug(
            "Airflow API DAG list response: status=%s, body=%s",
            resp.status_code, resp.text
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('dags', [])

    def get_dag_runs_by_id(
            self, dag_id, execution_date=None, threshold_date=None):
        """
        Retrieves dag runs for a specific dag_id using
        the Airflow v2 REST API.
        If threshold_date is provided, uses the batch
        POST endpoint with logical_date_gte.
        Otherwise, falls back to GET for all dag runs.
        If both execution_date and threshold_date are None,
        uses threshold_date = now - 30 days.
        If execution_date is not None, sets both
        logical_date_gte and logical_date_lte to execution_date.
        """
        web_server_url = self.web_server_url
        headers = self._get_headers()

        # If neither execution_date nor threshold_date is set,
        # use threshold_date = now - 30 days
        if not execution_date and not threshold_date:
            threshold_date = pendulum.now("UTC").subtract(days=30)

        if execution_date:
            # Use batch POST endpoint with both gte and
            # lte set to execution_date
            url = os.path.join(web_server_url, 'api/v2/dags/~/dagRuns/list')
            payload = {
                "page_offset": 0,
                "page_limit": 1000,
                "dag_ids": [dag_id],
                "logical_date_gte": execution_date,
                "logical_date_lte": execution_date
            }
            LOG.info("Requesting batch dagRuns for dag_id='%s' "
                     "with logical_date_gte and logical_date_lte='%s'",
                     dag_id, execution_date)
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=(self.c_timeout, self.r_timeout)
            )
            LOG.debug(
                "Airflow API batch dagRuns response: status=%s, body=%s",
                resp.status_code, resp.text
            )
            resp.raise_for_status()
            data = resp.json()
            dag_runs = data.get('dag_runs', [])
        elif threshold_date:
            # Ensure threshold_date is timezone-aware
            if threshold_date.tzinfo is None:
                threshold_date = threshold_date.replace(tzinfo=pytz.UTC)
            # Use batch POST endpoint for filtering
            url = os.path.join(web_server_url, 'api/v2/dags/~/dagRuns/list')
            payload = {
                "page_offset": 0,
                "page_limit": 1000,
                "dag_ids": [dag_id],
                "logical_date_gte": threshold_date.isoformat()
            }
            LOG.info("Requesting batch dagRuns for dag_id='%s' "
                     "with threshold_date='%s'", dag_id, threshold_date)
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=(self.c_timeout, self.r_timeout)
            )
            LOG.debug(
                "Airflow API batch dagRuns response: status=%s, body=%s",
                resp.status_code, resp.text
            )
            resp.raise_for_status()
            data = resp.json()
            dag_runs = data.get('dag_runs', [])
        else:
            # Fallback to GET for all dag runs
            dag_runs_url = os.path.join(
                web_server_url, f'api/v2/dags/{dag_id}/dagRuns?limit=1000'
            )
            LOG.info("Requesting dag runs for "
                     "dag_id='%s' (no threshold_date)", dag_id)
            resp = requests.get(
                dag_runs_url,
                timeout=(self.c_timeout, self.r_timeout),
                headers=headers
            )
            LOG.debug(
                "Airflow API dagRuns response: status=%s, body=%s",
                resp.status_code, resp.text
            )
            resp.raise_for_status()
            data = resp.json()
            dag_runs = data.get('dag_runs', [])

        # Filter by execution_date if provided
        result = []
        for run in dag_runs:
            if (execution_date is None) or (
                    run.get('logical_date') == execution_date):
                result.append({
                    "id": run.get("dag_run_id"),
                    "dag_id": run.get("dag_id"),
                    "state": run.get("state"),
                    "run_id": run.get("dag_run_id"),
                    "dag_run_id": run.get("dag_run_id"),
                    "execution_date": run.get("logical_date"),
                    "external_trigger": run.get("external_trigger"),
                    "conf": run.get("conf"),
                    "end_date": run.get("end_date"),
                    "start_date": run.get("start_date"),
                })
        LOG.info(
            "Found %d dag runs for dag_id='%s', "
            "execution_date='%s', threshold_date='%s'",
            len(result), dag_id, execution_date, threshold_date
        )
        return result

    def get_dag_runs_like_id(self, dag_id_prefix, execution_date=None):
        """
        Returns dag_runs for all DAGs whose id starts with dag_id_prefix,
        and (optionally) with the specified execution_date.
        """
        web_server_url = self.web_server_url
        headers = self._get_headers()

        LOG.info(
            "Requesting dag runs for DAGs with"
            "prefix '%s', execution_date='%s'",
            dag_id_prefix, execution_date
        )

        dag_list_url = os.path.join(
            web_server_url, 'api/v2/dags?limit=10000'
        )
        LOG.debug("Requesting DAG list from URL: %s", dag_list_url)
        dag_resp = requests.get(
            dag_list_url,
            timeout=(self.c_timeout, self.r_timeout),
            headers=headers
        )
        LOG.debug(
            "Airflow API DAG list response: status=%s, body=%s",
            dag_resp.status_code, dag_resp.text
        )
        dag_resp.raise_for_status()
        dag_data = dag_resp.json()
        dag_ids = [
            d['dag_id'] for d in dag_data.get('dags', [])
            if d['dag_id'].startswith(dag_id_prefix)
        ]

        dag_runs = []
        for dag_id in dag_ids:
            dag_runs_url = os.path.join(
                web_server_url,
                f'api/v2/dags/{dag_id}/dagRuns?limit=10000'
            )
            LOG.debug(
                "Requesting dag_runs from URL: %s", dag_runs_url
            )
            runs_resp = requests.get(
                dag_runs_url,
                timeout=(self.c_timeout, self.r_timeout),
                headers=headers
            )
            LOG.debug(
                "Airflow API dagRuns response: status=%s, body=%s",
                runs_resp.status_code, runs_resp.text
            )
            runs_resp.raise_for_status()
            runs_data = runs_resp.json()

            # If execution_date is None, return all dag_runs
            if execution_date is None:
                LOG.info(
                    "Returning all dag_runs for dag_id='%s'", dag_id
                )
                return runs_data.get('dag_runs', [])

            for run in runs_data.get('dag_runs', []):
                if run.get('logical_date') == execution_date:
                    dag_runs.append({
                        "id": run.get("dag_run_id"),
                        "dag_id": run.get("dag_id"),
                        "state": run.get("state"),
                        "run_id": run.get("dag_run_id"),
                        "execution_date": run.get("logical_date"),
                        "external_trigger": run.get("external_trigger"),
                        "conf": run.get("conf"),
                        "end_date": run.get("end_date"),
                        "start_date": run.get("start_date"),
                    })
        LOG.info(
            "Found %d dag runs for prefix '%s' and execution_date='%s'",
            len(dag_runs), dag_id_prefix, execution_date
        )
        return dag_runs

    def get_tasks_by_id(self, dag_id, execution_date=None):
        """
        Retrieves all tasks for a specific dag_id and
        (optionally) execution_date using the Airflow v2 REST API.
        Returns a list of task dictionaries.
        """
        web_server_url = CONF.base.web_server
        token_url = os.path.join(web_server_url, 'auth/token')
        c_timeout = CONF.base.airflow_api_connect_timeout
        r_timeout = CONF.base.airflow_api_read_timeout

        LOG.info(
            "Requesting tasks for dag_id='%s', execution_date='%s'",
            dag_id, execution_date
        )

        token_resp = requests.get(token_url, timeout=(c_timeout, r_timeout))
        token_resp.raise_for_status()
        token = token_resp.json().get('access_token')
        if not token:
            raise ApiError(
                title='Unable to retrieve JWT token',
                description='Airflow did not return a valid access token.',
                status=falcon.HTTP_503,
                retry=True,
            )
        headers = {
            'Cache-Control': 'no-cache',
            'Authorization': f'Bearer {token}'
        }

        dag_runs = self.get_dag_runs_by_id(dag_id, execution_date)
        LOG.debug("Found dag_runs for tasks: %s", dag_runs)
        if not dag_runs:
            LOG.warning(
                "No dag_run found for dag_id='%s' and execution_date='%s'",
                dag_id, execution_date
            )
            return []

        all_tasks = []
        for dag_run in dag_runs:
            dag_run_id = dag_run.get('run_id')
            task_instances_url = os.path.join(
                web_server_url,
                f'api/v2/dags/{dag_id}/dagRuns/{dag_run_id}'
                f'/taskInstances?limit=10000'
            )
            LOG.debug(
                "Requesting task instances from URL: %s",
                task_instances_url
            )
            ti_resp = requests.get(
                task_instances_url,
                timeout=(c_timeout, r_timeout),
                headers=headers
            )
            LOG.debug(
                "Airflow API taskInstances response: status=%s, body=%s",
                ti_resp.status_code, ti_resp.text
            )
            ti_resp.raise_for_status()
            ti_data = ti_resp.json()

            for ti in ti_data.get('task_instances', []):
                all_tasks.append({
                    'id': ti.get('id'),
                    'task_id': ti.get('task_id'),
                    'dag_id': ti.get('dag_id'),
                    'dag_run_id': ti.get('dag_run_id'),
                    'map_index': ti.get('map_index'),
                    'logical_date': ti.get('logical_date'),
                    'run_after': ti.get('run_after'),
                    'start_date': ti.get('start_date'),
                    'end_date': ti.get('end_date'),
                    'duration': ti.get('duration'),
                    'state': ti.get('state'),
                    'try_number': ti.get('try_number'),
                    'max_tries': ti.get('max_tries'),
                    'task_display_name': ti.get('task_display_name'),
                    'hostname': ti.get('hostname'),
                    'unixname': ti.get('unixname'),
                    'pool': ti.get('pool'),
                    'pool_slots': ti.get('pool_slots'),
                    'queue': ti.get('queue'),
                    'priority_weight': ti.get('priority_weight'),
                    'operator': ti.get('operator'),
                    'queued_when': ti.get('queued_when'),
                    'scheduled_when': ti.get('scheduled_when'),
                    'pid': ti.get('pid'),
                    'executor': ti.get('executor'),
                    'executor_config': ti.get('executor_config'),
                    'note': ti.get('note'),
                    'rendered_map_index': ti.get('rendered_map_index'),
                    'rendered_fields': ti.get('rendered_fields'),
                    'trigger': ti.get('trigger'),
                    'triggerer_job': ti.get('triggerer_job'),
                    'dag_version': ti.get('dag_version'),
                    'execution_date': ti.get('logical_date'),
                    'run_id': ti.get('dag_run_id'),
                    'job_id': None,
                    'queued_dttm': ti.get('queued_when'),
                })
        LOG.info(
            "Received %d tasks for dag_id='%s', execution_date='%s'",
            len(all_tasks), dag_id, execution_date
        )
        return all_tasks

    def check_dag_run_state(self, dag_id, execution_date, expected_state):
        """
        Examines a dag_run for state using the Airflow API.
        Throws AirflowStateError if it's not as expected or does not exist.
        """
        LOG.info(
            "Checking dag_run state for dag_id='%s', execution_date='%s', "
            "expected_state='%s'", dag_id, execution_date, expected_state
        )

        dag_run_list = self.get_dag_runs_by_id(
            dag_id=dag_id, execution_date=execution_date)
        LOG.debug("Found dag_run_list: %s", dag_run_list)

        if dag_run_list:
            dag_run = dag_run_list[0]
            if dag_run['state'] != expected_state:
                LOG.warning(
                    "dag_run state mismatch: expected '%s', got '%s'",
                    expected_state, dag_run['state']
                )
                raise AirflowStateError(
                    message=f"dag_run state must be {expected_state}, "
                            f"but is {dag_run['state']}"
                )
        else:
            LOG.error(
                "dag_run does not exist for dag_id='%s', execution_date='%s'",
                dag_id, execution_date
            )
            raise AirflowStateError(message='dag_run does not exist')
        return True

    def _set_dag_run_state(self, state, dag_id, execution_date):
        """
        Sets a dag run to the specified state using
        the Airflow API v2.
        Airflow API v2 does not provide a direct
        endpoint to PATCH dag_run state,
        but you can use the updateDagRun endpoint.
        """
        web_server_url = self.web_server_url
        headers = self._get_headers()

        LOG.info(
            "Setting dag_run state for dag_id='%s', "
            "execution_date='%s' to '%s'",
            dag_id, execution_date, state
        )
        dag_runs = self.get_dag_runs_by_id(dag_id, execution_date)
        LOG.debug("Found dag_runs: %s", dag_runs)
        if not dag_runs:
            LOG.error(
                "No dag_run found for dag_id='%s' and execution_date='%s'",
                dag_id, execution_date
            )
            raise ApiError(
                title='DAG Run Not Found',
                description=(
                    f'No dag_run found for dag_id={dag_id} and '
                    f'execution_date={execution_date}'
                ),
                status=404
            )
        dag_run_id = dag_runs[0]['run_id']

        dag_run_url = os.path.join(
            web_server_url, f'api/v2/dags/{dag_id}/dagRuns/{dag_run_id}'
        )
        payload = {"state": state}
        LOG.debug("PATCH %s with payload: %s", dag_run_url, payload)

        resp = requests.patch(
            dag_run_url,
            json=payload,
            headers=headers,
            timeout=(self.c_timeout, self.r_timeout)
        )
        LOG.debug(
            "Airflow API PATCH response: status=%s, body=%s",
            resp.status_code, resp.text
        )
        if resp.status_code not in (200, 204):
            LOG.error(
                "Failed to update dag_run state: %s", resp.text
            )
            raise ApiError(
                title='Failed to update dag_run state',
                description=(
                    f'Airflow API returned {resp.status_code}: {resp.text}'
                ),
                status=resp.status_code
            )
        LOG.info(
            "Successfully set dag_run state for dag_id='%s', "
            "execution_date='%s' to '%s'",
            dag_id, execution_date, state
        )
        return resp.json() if resp.content else {}

    def _control_dag_run(
            self, dag_id, execution_date, expected_state, desired_state):
        """
        Checks a dag_run's state for the expected state, and sets it to the
        desired state using the Airflow API.
        """
        self.check_dag_run_state(
            dag_id=dag_id,
            execution_date=execution_date,
            expected_state=expected_state
        )
        self._set_dag_run_state(
            state=desired_state,
            dag_id=dag_id,
            execution_date=execution_date
        )

    def stop_dag_run(self, dag_id, execution_date):
        """
        Triggers an update to set a dag_run to failed state,
        causing dag_run to be stopped.
        running -> failed
        """
        LOG.info(
            "Stopping dag_run for dag_id='%s', "
            "execution_date='%s' (running -> failed)",
            dag_id, execution_date
        )
        self._control_dag_run(
            dag_id=dag_id,
            execution_date=execution_date,
            expected_state='running',
            desired_state='failed'
        )

    def invoke_airflow_dag(self, dag_id, action, context):
        """
        Call Airflow and invoke a DAG using the Airflow REST API v1 with JWT
        authentication.
        :param dag_id: the name of the DAG to invoke
        :param action: the action structure to invoke the DAG with
        """
        # Retrieve Airflow web server URL
        web_server_url = CONF.base.web_server
        api_path = 'api/v2/dags/{}/dagRuns?limit=10000'
        req_url = os.path.join(web_server_url, api_path.format(dag_id))
        token_url = os.path.join(web_server_url, 'auth/token')
        c_timeout = CONF.base.airflow_api_connect_timeout
        r_timeout = CONF.base.airflow_api_read_timeout

        if 'Error' in web_server_url:
            raise ApiError(
                title='Unable to invoke workflow',
                description=(
                    'Airflow URL not found by Shipyard. '
                    'Shipyard configuration is missing web_server value'),
                status=falcon.HTTP_503,
                retry=True,
            )

        try:
            # Step 1: Retrieve the JWT token
            token_resp = requests.get(token_url,
                                      timeout=(c_timeout, r_timeout))
            token_resp.raise_for_status()
            token = token_resp.json().get('access_token')
            if not token:
                raise ApiError(
                    title='Unable to retrieve JWT token',
                    description='Airflow did not return a valid access token.',
                    status=falcon.HTTP_503,
                    retry=True,
                )

            # Step 2: Prepare headers with the token
            headers = {
                'Cache-Control': 'no-cache',
                'Authorization': f'Bearer {token}'
            }

            # Step 3: Prepare the payload

            # Generate current UTC time with timezone info
            logical_date = pendulum.now("UTC").to_iso8601_string()
            payload = {
                'dag_run_id': action['id'],
                'logical_date': logical_date,
                'conf': {
                    'action': action
                }
            }
            LOG.info('Request payload: %s', payload)

            # Step 4: Make the POST request to trigger the DAG
            resp = requests.post(req_url,
                                 timeout=(c_timeout, r_timeout),
                                 headers=headers,
                                 json=payload)
            LOG.info('Response code from Airflow trigger_dag: %s',
                     resp.status_code)
            resp.raise_for_status()
            response = resp.json()
            LOG.info('Response from Airflow trigger_dag: %s', response)

            # Step 5: Extract and return the DAG execution date (logical_date)
            dag_execution_date = response.get('logical_date')
            if not dag_execution_date:
                raise ApiError(
                    title='Unable to determine DAG execution date',
                    description='Airflow did not return a valid logical_date.',
                    status=falcon.HTTP_503,
                    retry=True,
                )
            return dag_execution_date

        except RequestException as rex:
            LOG.error("Request to Airflow failed: %s", rex.args)
            raise ApiError(
                title='Unable to complete request to Airflow',
                description=(
                    'Airflow could not be contacted properly by Shipyard.'),
                status=falcon.HTTP_503,
                error_list=[{
                    'message': str(type(rex))
                }],
                retry=True,
            )
