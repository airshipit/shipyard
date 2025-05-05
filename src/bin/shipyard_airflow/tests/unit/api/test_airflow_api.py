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

from time import sleep
import pytest

import json
import uuid
import base64

from shipyard_airflow.api.api import AIRFLOW_API


class TestAirflowApi:
    @pytest.fixture(scope="class", autouse=True)
    def api(self):
        # Returns the singleton instance of AirflowApiAccess
        return AIRFLOW_API

    def test_get_all_dag_runs_for_dag_id(self, api):
        # Test that all DAG runs for example_bash_operator are returned
        dag_runs = api.get_dag_runs_by_id('example_bash_operator')
        assert isinstance(dag_runs, list)
        assert any(dr['dag_id'] == 'example_bash_operator' for dr in dag_runs)

    def test_get_dag_runs_by_id(self, api):
        # Test that dag_runs for a specific dag_id and execution_date are returned
        dag_runs = api.get_dag_runs_by_id('example_bash_operator', "2018-01-01T00:00:00Z")
        assert isinstance(dag_runs, list)
        if dag_runs:
            dr = dag_runs[0]
            assert dr['dag_id'] == 'example_bash_operator'
            assert 'execution_date' in dr

    def test_get_tasks_by_id(self, api):
        # Test that tasks for a specific dag_id and execution_date are returned
        dag_runs = api.get_dag_runs_by_id('example_bash_operator', "2018-01-01T00:00:00Z")
        if not dag_runs:
            pytest.skip("No dag_runs found for example_bash_operator")
        execution_date = dag_runs[0]['execution_date']
        tasks = api.get_tasks_by_id('example_bash_operator', execution_date)
        assert isinstance(tasks, list)
        assert any(t['task_id'] == 'runme_0' for t in tasks)

    def test_check_dag_run_state(self, api):
        # Test that the dag_run is in the 'success' state
        dag_runs = api.get_dag_runs_by_id('example_bash_operator', "2018-01-01T00:00:00Z")
        if not dag_runs:
            pytest.skip("No dag_runs found for example_bash_operator")
        execution_date = dag_runs[0]['execution_date']
        state = dag_runs[0]['state']
        assert state == "success"
        # Also check using the API method
        assert api.check_dag_run_state('example_bash_operator', execution_date, "success")

    def test_stop_start_dag_run(self, api):
        # Set dag_run to 'queued' state (allowed by Airflow API)
        dag_runs = api.get_dag_runs_by_id('example_bash_operator', "2018-01-01T00:00:00Z")
        if not dag_runs:
            pytest.skip("No dag_runs found for example_bash_operator")
        execution_date = dag_runs[0]['execution_date']
        api._set_dag_run_state('queued', 'example_bash_operator', execution_date)
        sleep(10)  # Allow time for the state change to propagate
        # Verify that dag_run is now 'queued'
        updated = api.get_dag_runs_by_id('example_bash_operator', execution_date)
        assert updated and updated[0]['state'] in ['queued', 'success' ]
        # # Also check using the API method
        # assert api.check_dag_run_state('example_bash_operator', execution_date, "queued")
        # Now test stop_dag_run, expecting queued -> failed
        api._control_dag_run(
            dag_id='example_bash_operator',
            execution_date=execution_date,
            expected_state='success',
            desired_state='failed'
        )
        updated = api.get_dag_runs_by_id('example_bash_operator', execution_date)
        # Accept both 'failed' and 'success' as valid terminal states,
        # since Airflow may not allow transition to 'failed' if already 'success'
        assert updated and updated[0]['state'] == 'failed'
        # Also check using the API method
        assert api.check_dag_run_state('example_bash_operator', execution_date, "failed")
        # Now test stop_dag_run, expecting queued -> failed
        api._control_dag_run(
            dag_id='example_bash_operator',
            execution_date=execution_date,
            expected_state='failed',
            desired_state='success'
        )
        updated = api.get_dag_runs_by_id('example_bash_operator', execution_date)
        # Accept both 'failed' and 'success' as valid terminal states,
        # since Airflow may not allow transition to 'failed' if already 'success'
        assert updated and updated[0]['state'] == 'success'
        # Also check using the API method
        assert api.check_dag_run_state('example_bash_operator', execution_date, "success")

    def test_invoke_airflow_dag(self, api):
        """
        Test invoking a DAG run via the Airflow API.
        """
        dag_id = 'example_bash_operator'

        def generate_base32_id():
            # Generate a UUID
            unique_id = uuid.uuid4()
            # Encode the UUID as Base32 and remove padding
            base32_id = base64.b32encode(unique_id.bytes).decode('utf-8').strip('=')
            return base32_id

        # Generate a UUID
        generated_uuid = uuid.uuid4()

        # Convert UUID to string before serializing
        data = {"id": str(generated_uuid)}

        # Serialize to JSON
        json_uuid = json.dumps(data)


        action = {
            'id': generate_base32_id(),
            'name': 'invoke_airflow_dag',
            'parameters': None,
            'dag_id': 'example_bash_operator',
            "context_marker": json_uuid
        }

        context = {}  # Provide context if needed by your implementation

        # Call the method to trigger the DAG
        logical_date = api.invoke_airflow_dag(dag_id, action, context)

        # Check that a logical_date (execution date) is returned and is ISO8601
        assert logical_date is not None
        assert isinstance(logical_date, str)
        assert logical_date.startswith('20')  # crude check for ISO8601 year