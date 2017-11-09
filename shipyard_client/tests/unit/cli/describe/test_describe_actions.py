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

from shipyard_client.cli.describe.actions import \
    DescribeAction, DescribeStep, DescribeValidation, DescribeWorkflow
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
    'shipyard_client.cli.describe.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_DescribeAction(*args):
    response = DescribeAction(
        ctx, '01BTG32JW87G0YKA1K29TKNAFX').invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'actions/01BTG32JW87G0YKA1K29TKNAFX' in url


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.describe.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_DescribeStep(*args):
    response = DescribeStep(ctx, '01BTG32JW87G0YKA1K29TKNAFX',
                            'preflight').invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'actions/01BTG32JW87G0YKA1K29TKNAFX/steps/preflight' in url


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.describe.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_DescribeValidation(*args):
    response = DescribeValidation(
        ctx, '01BTG32JW87G0YKA1K29TKNAFX',
        '01BTG3PKBS15KCKFZ56XXXBGF2').invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'actions' in url
    assert '01BTG32JW87G0YKA1K29TKNAFX' in url
    assert 'validationdetails' in url
    assert '01BTG3PKBS15KCKFZ56XXXBGF2' in url


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
@mock.patch.object(ShipyardClientContext, '__init__', temporary_context)
@mock.patch(
    'shipyard_client.cli.describe.actions.output_formatting',
    side_effect=replace_output_formatting)
def test_DescribeWorkflow(*args):
    response = DescribeWorkflow(
        ctx, 'deploy_site__2017-01-01T12:34:56.123456'
    ).invoke_and_return_resp()
    # test correct function was called
    url = response.get('url')
    assert 'workflows' in url
    assert 'deploy_site__2017-01-01T12:34:56.123456' in url
