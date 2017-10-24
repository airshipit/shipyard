# -*- coding: utf-8 -*-
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

import mock
import json

from shipyard_client.api_client.shipyard_api_client import ShipyardClient
from shipyard_client.api_client.base_client import BaseClient


class TemporaryContext:
    def __init__(self):
        self.debug = True
        self.keystone_Auth = {}
        self.token = 'abcdefgh'
        self.service_type = 'http://shipyard'
        self.shipyard_endpoint = 'http://shipyard/api/v1.0'
        self.context_marker = '123456'


def replace_post_rep(self, url, query_params={}, data={}, content_type=''):
    """
    replaces call to shipyard client
    :returns: dict with url and parameters
    """
    return {'url': url, 'params': query_params, 'data': data}


def replace_get_resp(self, url, query_params={}, json=False):
    """
    replaces call to shipyard client
    :returns: dict with url and parameters
    """
    return {'url': url, 'params': query_params}


def replace_base_constructor(self, context):
    pass


def get_api_client():
    """
    get a instance of shipyard client
    :returns: shipyard client with no context object
    """
    context = TemporaryContext()
    return ShipyardClient(context)


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_post_config_docs(*args):
    shipyard_client = get_api_client()
    buffermode = 'rejectoncontents'
    result = shipyard_client.post_configdocs('ABC', buffer_mode=buffermode)
    params = result['params']
    assert result['url'] == '{}/configdocs/ABC'.format(
        shipyard_client.shipyard_url)
    assert params['buffermode'] == buffermode


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_get_config_docs(*args):
    shipyard_client = get_api_client()
    version = 'buffer'
    result = shipyard_client.get_configdocs('ABC', version=version)
    params = result['params']
    assert result['url'] == '{}/configdocs/ABC'.format(
        shipyard_client.shipyard_url)
    assert params['version'] == version


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_rendered_config_docs(*args):
    shipyard_client = get_api_client()
    version = 'buffer'
    result = shipyard_client.get_rendereddocs(version=version)
    params = result['params']
    assert result['url'] == '{}/renderedconfigdocs'.format(
        shipyard_client.shipyard_url)
    assert params['version'] == version


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_commit_configs(*args):
    shipyard_client = get_api_client()
    force_mode = True
    result = shipyard_client.commit_configdocs(force_mode)
    params = result['params']
    assert result['url'] == '{}/commitconfigdocs'.format(
        shipyard_client.shipyard_url)
    assert params['force'] == force_mode


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_get_actions(*args):
    shipyard_client = get_api_client()
    result = shipyard_client.get_actions()
    assert result['url'] == '{}/actions'.format(
        shipyard_client.shipyard_url)


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_post_actions(*args):
    shipyard_client = get_api_client()
    name = 'good action'
    parameters = {'hello': 'world'}
    result = shipyard_client.post_actions(name, parameters)
    data = json.loads(result['data'])
    assert result['url'] == '{}/actions'.format(
        shipyard_client.shipyard_url)
    assert data['name'] == name
    assert data['parameters']['hello'] == 'world'


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_action_details(*args):
    shipyard_client = get_api_client()
    action_id = 'GoodAction'
    result = shipyard_client.get_action_detail(action_id)
    assert result['url'] == '{}/actions/{}'.format(
        shipyard_client.shipyard_url, action_id)


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_get_val_details(*args):
    shipyard_client = get_api_client()
    action_id = 'GoodAction'
    validation_id = 'Validation'
    result = shipyard_client.get_validation_detail(action_id, validation_id)
    assert result[
        'url'] == '{}/actions/{}/validationdetails/{}'.format(
            shipyard_client.shipyard_url, action_id, validation_id)


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_get_step_details(*args):
    shipyard_client = get_api_client()
    action_id = 'GoodAction'
    step_id = 'TestStep'
    result = shipyard_client.get_step_detail(action_id, step_id)
    assert result['url'] == '{}/actions/{}/steps/{}'.format(
        shipyard_client.shipyard_url, action_id, step_id)


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_post_control(*args):
    shipyard_client = get_api_client()
    action_id = 'GoodAction'
    control_verb = 'Control'
    result = shipyard_client.post_control_action(action_id, control_verb)
    assert result['url'] == '{}/actions/{}/control/{}'.format(
        shipyard_client.shipyard_url, action_id, control_verb)


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_get_workflows(*args):
    shipyard_client = get_api_client()
    since_mode = 'TestSince'
    result = shipyard_client.get_workflows(since_mode)
    assert result['url'] == '{}/workflows'.format(
        shipyard_client.shipyard_url, since_mode)


@mock.patch.object(BaseClient, '__init__', replace_base_constructor)
@mock.patch.object(BaseClient, 'post_resp', replace_post_rep)
@mock.patch.object(BaseClient, 'get_resp', replace_get_resp)
def test_get_dag_details(*args):
    shipyard_client = get_api_client()
    workflow_id = 'TestWorkflow'
    result = shipyard_client.get_dag_detail(workflow_id)
    assert result['url'] == '{}/workflows/{}'.format(
        shipyard_client.shipyard_url, workflow_id)
