# Copyright 2017 AT&T Intellectual Property. All other rights reserved.
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
import mock

import responses

from shipyard_client.api_client.base_client import BaseClient
from shipyard_client.cli.describe.actions import DescribeAction
from shipyard_client.cli.describe.actions import DescribeStep
from shipyard_client.cli.describe.actions import DescribeValidation
from shipyard_client.cli.describe.actions import DescribeWorkflow
from shipyard_client.tests.unit.cli import stubs


GET_ACTION_API_RESP = """
{
  "name": "deploy_site",
  "dag_execution_date": "2017-09-24T19:05:49",
  "validations": [],
  "id": "01BTTMFVDKZFRJM80FGD7J1AKN",
  "dag_id": "deploy_site",
  "command_audit": [
    {
      "id": "01BTTMG16R9H3Z4JVQNBMRV1MZ",
      "action_id": "01BTTMFVDKZFRJM80FGD7J1AKN",
      "datetime": "2017-09-24 19:05:49.530223+00:00",
      "user": "shipyard",
      "command": "invoke"
    }
  ],
  "user": "shipyard",
  "context_marker": "629f2ea2-c59d-46b9-8641-7367a91a7016",
  "datetime": "2017-09-24 19:05:43.603591+00:00",
  "dag_status": "failed",
  "parameters": {},
  "steps": [
    {
      "id": "action_xcom",
      "url": "/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/action_xcom",
      "index": 1,
      "state": "success"
    }
  ],
  "action_lifecycle": "Failed"
}
"""


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_action(*args):
    responses.add(responses.GET,
                  'http://shiptest/actions/01BTTMFVDKZFRJM80FGD7J1AKN',
                  body=GET_ACTION_API_RESP,
                  status=200)

    response = DescribeAction(
        stubs.StubCliContext(),
        '01BTTMFVDKZFRJM80FGD7J1AKN'
    ).invoke_and_return_resp()
    assert 'action/01BTTMFVDKZFRJM80FGD7J1AKN' in response
    assert 'step/01BTTMFVDKZFRJM80FGD7J1AKN/action_xcom' in response
    assert 'Steps' in response
    assert 'Commands' in response
    assert 'Validations:' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_action_not_found(*args):
    api_resp = stubs.gen_err_resp(message='Not Found',
                                  sub_error_count=0,
                                  sub_info_count=0,
                                  reason='It does not exist',
                                  code=404)
    responses.add(responses.GET,
                  'http://shiptest/actions/01BTTMFVDKZFRJM80FGD7J1AKN',
                  body=api_resp,
                  status=404)

    response = DescribeAction(
        stubs.StubCliContext(),
        '01BTTMFVDKZFRJM80FGD7J1AKN'
    ).invoke_and_return_resp()
    assert 'Error: Not Found' in response
    assert 'Reason: It does not exist' in response


GET_STEP_API_RESP = """
{
  "end_date": "2017-09-24 19:05:59.446213",
  "duration": 0.165181,
  "queued_dttm": "2017-09-24 19:05:52.993983",
  "operator": "PythonOperator",
  "try_number": 1,
  "task_id": "preflight",
  "state": "success",
  "execution_date": "2017-09-24 19:05:49",
  "dag_id": "deploy_site",
  "index": 1,
  "start_date": "2017-09-24 19:05:59.281032"
}
"""


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_step(*args):
    responses.add(
        responses.GET,
        'http://shiptest/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/preflight',
        body=GET_STEP_API_RESP,
        status=200)

    response = DescribeStep(stubs.StubCliContext(),
                            '01BTTMFVDKZFRJM80FGD7J1AKN',
                            'preflight').invoke_and_return_resp()
    assert 'step/01BTTMFVDKZFRJM80FGD7J1AKN/preflight' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_step_not_found(*args):
    api_resp = stubs.gen_err_resp(message='Not Found',
                                  sub_error_count=0,
                                  sub_info_count=0,
                                  reason='It does not exist',
                                  code=404)
    responses.add(
        responses.GET,
        'http://shiptest/actions/01BTTMFVDKZFRJM80FGD7J1AKN/steps/preflight',
        body=api_resp,
        status=404)

    response = DescribeStep(stubs.StubCliContext(),
                            '01BTTMFVDKZFRJM80FGD7J1AKN',
                            'preflight').invoke_and_return_resp()
    assert 'Error: Not Found' in response
    assert 'Reason: It does not exist' in response


GET_VALIDATION_API_RESP = """
{
  "validation_name": "validation_1",
  "action_id": "01BTTMFVDKZFRJM80FGD7J1AKN",
  "id": "02AURNEWAAAESKN99EBF8J2BHD",
  "details": "Validations failed for field 'abc'"
}
"""


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_validation(*args):
    responses.add(
        responses.GET,
        'http://shiptest/actions/01BTTMFVDKZFRJM80FGD7J1AKN/'
        'validationdetails/02AURNEWAAAESKN99EBF8J2BHD',
        body=GET_VALIDATION_API_RESP,
        status=200)

    response = DescribeValidation(
        stubs.StubCliContext(),
        action_id='01BTTMFVDKZFRJM80FGD7J1AKN',
        validation_id='02AURNEWAAAESKN99EBF8J2BHD').invoke_and_return_resp()

    v_str = "validation/01BTTMFVDKZFRJM80FGD7J1AKN/02AURNEWAAAESKN99EBF8J2BHD"
    assert v_str in response
    assert "Validations failed for field 'abc'" in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_validation_not_found(*args):
    api_resp = stubs.gen_err_resp(message='Not Found',
                                  sub_error_count=0,
                                  sub_info_count=0,
                                  reason='It does not exist',
                                  code=404)
    responses.add(
        responses.GET,
        'http://shiptest/actions/01BTTMFVDKZFRJM80FGD7J1AKN/'
        'validationdetails/02AURNEWAAAESKN99EBF8J2BHD',
        body=api_resp,
        status=404)

    response = DescribeValidation(
        stubs.StubCliContext(),
        action_id='01BTTMFVDKZFRJM80FGD7J1AKN',
        validation_id='02AURNEWAAAESKN99EBF8J2BHD').invoke_and_return_resp()
    assert 'Error: Not Found' in response
    assert 'Reason: It does not exist' in response


WF_API_RESP = """
{
  "execution_date": "2017-10-09 21:19:03",
  "end_date": null,
  "workflow_id": "deploy_site__2017-10-09T21:19:03.000000",
  "start_date": "2017-10-09 21:19:03.361522",
  "external_trigger": true,
  "steps": [
    {
      "end_date": "2017-10-09 21:19:14.916220",
      "task_id": "action_xcom",
      "start_date": "2017-10-09 21:19:14.798053",
      "duration": 0.118167,
      "queued_dttm": "2017-10-09 21:19:08.432582",
      "try_number": 1,
      "state": "success",
      "operator": "PythonOperator",
      "dag_id": "deploy_site",
      "execution_date": "2017-10-09 21:19:03"
    },
    {
      "end_date": "2017-10-09 21:19:25.283785",
      "task_id": "dag_concurrency_check",
      "start_date": "2017-10-09 21:19:25.181492",
      "duration": 0.102293,
      "queued_dttm": "2017-10-09 21:19:19.283132",
      "try_number": 1,
      "state": "success",
      "operator": "ConcurrencyCheckOperator",
      "dag_id": "deploy_site",
      "execution_date": "2017-10-09 21:19:03"
    },
    {
      "end_date": "2017-10-09 21:20:05.394677",
      "task_id": "preflight",
      "start_date": "2017-10-09 21:19:34.994775",
      "duration": 30.399902,
      "queued_dttm": "2017-10-09 21:19:28.449848",
      "try_number": 1,
      "state": "failed",
      "operator": "SubDagOperator",
      "dag_id": "deploy_site",
      "execution_date": "2017-10-09 21:19:03"
    }
  ],
  "dag_id": "deploy_site",
  "state": "failed",
  "run_id": "manual__2017-10-09T21:19:03",
  "sub_dags": [
    {
      "execution_date": "2017-10-09 21:19:03",
      "end_date": null,
      "workflow_id": "deploy_site.preflight__2017-10-09T21:19:03.000000",
      "start_date": "2017-10-09 21:19:35.082479",
      "external_trigger": false,
      "dag_id": "deploy_site.preflight",
      "state": "failed",
      "run_id": "backfill_2017-10-09T21:19:03"
    },
    {
      "execution_date": "2017-10-09 21:19:03",
      "end_date": null,
      "workflow_id": "deploy_site.postflight__2017-10-09T21:19:03.000000",
      "start_date": "2017-10-09 21:19:35.082479",
      "external_trigger": false,
      "dag_id": "deploy_site.postflight",
      "state": "failed",
      "run_id": "backfill_2017-10-09T21:19:03"
    }
  ]
}
"""


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_workflow(*args):
    responses.add(
        responses.GET,
        'http://shiptest/workflows/deploy_site__2017-10-09T21:19:03.000000',
        body=WF_API_RESP,
        status=200)

    response = DescribeWorkflow(
        stubs.StubCliContext(),
        'deploy_site__2017-10-09T21:19:03.000000'
    ).invoke_and_return_resp()
    assert 'deploy_site__2017-10-09T21:19:03.000000' in response
    assert 'deploy_site.preflight__2017-10-09T21:19:03.000000' in response
    assert 'deploy_site.postflight__2017-10-09T21:19:03.000000' in response
    assert 'dag_concurrency_check' in response
    assert 'Subworkflows:' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_describe_workflow_not_found(*args):
    api_resp = stubs.gen_err_resp(message='Not Found',
                                  sub_error_count=0,
                                  sub_info_count=0,
                                  reason='It does not exist',
                                  code=404)
    responses.add(
        responses.GET,
        'http://shiptest/workflows/deploy_site__2017-10-09T21:19:03.000000',
        body=api_resp,
        status=404)

    response = DescribeWorkflow(
        stubs.StubCliContext(),
        'deploy_site__2017-10-09T21:19:03.000000'
    ).invoke_and_return_resp()
    assert 'Error: Not Found' in response
    assert 'Reason: It does not exist' in response
