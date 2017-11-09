# Copyright 2017 AT&T Intellectual Property. replace_shipyard  All other rights
# reserved.
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

from shipyard_client.cli.get.actions import GetActions, GetConfigdocs, \
    GetRenderedConfigdocs, GetWorkflows
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
    'context_marker': '88888888-4444-4444-4444-121212121212',
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
    'shipyard_client.cli.get.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_GetActions(*args):
    response = GetActions(ctx).invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'actions' in url
    assert response.get('params') == {}


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.get.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_GetConfigdocs(*args):
    response = GetConfigdocs(ctx, 'design', 'buffer').invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'configdocs/design' in url
    params = response.get('params')
    assert params.get('version') == 'buffer'


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.get.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_GetRenderedConfigdocs(*args):
    response = GetRenderedConfigdocs(ctx, 'buffer').invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'renderedconfigdocs' in url
    params = response.get('params')
    assert params.get('version') == 'buffer'


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.get.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_GetWorkflows(*args):
    response = GetWorkflows(ctx, since=None).invoke_and_return_resp()
    url = response.get('url')
    assert 'workflows' in url
    assert 'since' not in url

    response = GetWorkflows(ctx).invoke_and_return_resp()
    url = response.get('url')
    assert 'workflows' in url
    assert 'since' not in url

    since_val = '2017-01-01T12:34:56Z'
    response = GetWorkflows(ctx,
                            since=since_val).invoke_and_return_resp()
    url = response.get('url')
    assert 'workflows' in url
    params = response.get('params')
    assert params.get('since') == since_val
