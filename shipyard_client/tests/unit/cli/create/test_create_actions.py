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

from shipyard_client.cli.create.actions import CreateAction, CreateConfigdocs
from shipyard_client.api_client.base_client import BaseClient
from shipyard_client.tests.unit.cli.replace_api_client import \
    replace_base_constructor, replace_post_rep, replace_get_resp, \
    replace_output_formatting
from shipyard_client.tests.unit.cli.utils import temporary_context
from shipyard_client.api_client.shipyardclient_context import \
    ShipyardClientContext

auth_vars = {
    'project_domain_name': 'projDomainTest',
    'user_domain_name': 'userDomainTest',
    'project_name': 'projectTest',
    'username': 'usernameTest',
    'password': 'passwordTest',
    'auth_url': 'urlTest'
}

api_parameters = {
    'auth_vars': auth_vars,
    'context_marker': 'UUID',
    'debug': False
}


class MockCTX():
    pass


ctx = MockCTX()
ctx.obj = {}
ctx.obj['API_PARAMETERS'] = api_parameters
ctx.obj['FORMAT'] = 'format'


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.create.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_CreateAction(*args):
    action_name = 'redeploy_server'
    param = {'server-name': 'mcp'}
    response = CreateAction(ctx, action_name, param).invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'actions' in url
    # test function was called with correct parameters
    data = response.get('data')
    assert '"name": "redeploy_server"' in data
    assert '"parameters": {"server-name": "mcp"}' in data


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.create.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_CreateConfigdocs(*args):
    collection = 'design'
    filename = 'shipyard_client/tests/unit/cli/create/sample_yaml/sample.yaml'
    document_data = yaml.dump_all(filename)
    buffer = 'append'
    response = CreateConfigdocs(ctx, collection, buffer,
                                document_data).invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'configdocs' in url
    # test function was called with correct parameters
    assert collection in url
    data = response.get('data')
    assert document_data in data
    params = response.get('params')
    assert params.get('buffermode') == buffer
