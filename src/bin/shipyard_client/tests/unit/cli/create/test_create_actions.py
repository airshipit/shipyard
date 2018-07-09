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
import yaml

import responses

from shipyard_client.api_client.base_client import BaseClient
from shipyard_client.cli.create.actions import CreateAction
from shipyard_client.cli.create.actions import CreateConfigdocs
from tests.unit.cli import stubs

resp_body = """
{
  "dag_status": "SCHEDULED",
  "parameters": {},
  "dag_execution_date": "2017-09-24T19:05:49",
  "id": "01BTTMFVDKZFRJM80FGD7J1AKN",
  "dag_id": "deploy_site",
  "name": "deploy_site",
  "user": "shipyard",
  "context_marker": "629f2ea2-c59d-46b9-8641-7367a91a7016",
  "timestamp": "2017-09-24 19:05:43.603591"
}
"""


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_create_action(*args):
    responses.add(responses.POST,
                  'http://shiptest/actions',
                  body=resp_body,
                  status=201)
    response = CreateAction(
        stubs.StubCliContext(),
        action_name='deploy_site',
        param=None,
        allow_intermediate_commits=False).invoke_and_return_resp()
    assert 'Name' in response
    assert 'Action' in response
    assert 'Lifecycle' in response
    assert 'action/01BTTMFVDKZFRJM80FGD7J1AKN' in response
    assert 'Error:' not in response
    assert '0/0/0' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_create_action_400(*args):
    responses.add(responses.POST,
                  'http://shiptest/actions',
                  body=stubs.gen_err_resp(message='Error_400',
                                          reason='bad action'),
                  status=400)
    response = CreateAction(
        stubs.StubCliContext(),
        action_name='deploy_dogs',
        param=None,
        allow_intermediate_commits=False).invoke_and_return_resp()
    assert 'Error_400' in response
    assert 'bad action' in response
    assert 'action/01BTTMFVDKZFRJM80FGD7J1AKN' not in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_create_action_409(*args):
    responses.add(responses.POST,
                  'http://shiptest/actions',
                  body=stubs.gen_err_resp(message='Error_409',
                                          reason='bad validations'),
                  status=409)
    response = CreateAction(
        stubs.StubCliContext(),
        action_name='deploy_site',
        param=None,
        allow_intermediate_commits=False).invoke_and_return_resp()
    assert 'Error_409' in response
    assert 'bad validations' in response
    assert 'action/01BTTMFVDKZFRJM80FGD7J1AKN' not in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_create_configdocs(*args):
    succ_resp = stubs.gen_err_resp(message='Validations succeeded',
                                   sub_error_count=0,
                                   sub_info_count=0,
                                   reason='Validation',
                                   code=200)
    responses.add(responses.POST,
                  'http://shiptest/configdocs/design',
                  body=succ_resp,
                  status=201)

    filename = 'tests/unit/cli/create/sample_yaml/sample.yaml'
    document_data = yaml.dump_all(filename)
    file_list = (filename,)

    response = CreateConfigdocs(stubs.StubCliContext(),
                                'design',
                                'append',
                                document_data,
                                file_list).invoke_and_return_resp()
    assert 'Configuration documents added.'
    assert 'Status: Validations succeeded' in response
    assert 'Reason: Validation' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_create_configdocs_201_with_val_fails(*args):
    succ_resp = stubs.gen_err_resp(message='Validations failed',
                                   sub_message='Some reason',
                                   sub_error_count=2,
                                   sub_info_count=1,
                                   reason='Validation',
                                   code=400)
    responses.add(responses.POST,
                  'http://shiptest/configdocs/design',
                  body=succ_resp,
                  status=201)

    filename = 'tests/unit/cli/create/sample_yaml/sample.yaml'
    document_data = yaml.dump_all(filename)
    file_list = (filename,)

    response = CreateConfigdocs(stubs.StubCliContext(),
                                'design',
                                'append',
                                document_data,
                                file_list).invoke_and_return_resp()
    assert 'Configuration documents added.' in response
    assert 'Status: Validations failed' in response
    assert 'Reason: Validation' in response
    assert 'Some reason-1' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_create_configdocs_409(*args):
    err_resp = stubs.gen_err_resp(message='Invalid collection',
                                  sub_message='Buffer is either not...',
                                  sub_error_count=1,
                                  sub_info_count=0,
                                  reason='Buffermode : append',
                                  code=409)
    responses.add(responses.POST,
                  'http://shiptest/configdocs/design',
                  body=err_resp,
                  status=409)

    filename = 'tests/unit/cli/create/sample_yaml/sample.yaml'
    document_data = yaml.dump_all(filename)
    file_list = (filename,)

    response = CreateConfigdocs(stubs.StubCliContext(),
                                'design',
                                'append',
                                document_data,
                                file_list).invoke_and_return_resp()
    assert 'Error: Invalid collection' in response
    assert 'Reason: Buffermode : append' in response
    assert 'Buffer is either not...' in response
