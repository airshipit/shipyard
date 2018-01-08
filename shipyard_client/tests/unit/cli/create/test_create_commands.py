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
from click.testing import CliRunner
from mock import patch, ANY

from shipyard_client.cli.create.actions import CreateAction, CreateConfigdocs
from shipyard_client.cli.commands import shipyard

auth_vars = ('--os-project-domain-name=OS_PROJECT_DOMAIN_NAME_test '
             '--os-user-domain-name=OS_USER_DOMAIN_NAME_test '
             '--os-project-name=OS_PROJECT_NAME_test '
             '--os-username=OS_USERNAME_test '
             '--os-password=OS_PASSWORD_test '
             '--os-auth-url=OS_AUTH_URL_test')


def test_create_action():
    """test create_action works with action id and param input"""

    action_name = 'redeploy_server'
    param = '--param="server-name=mcp"'
    runner = CliRunner()
    with patch.object(CreateAction, '__init__') as mock_method:
        runner.invoke(shipyard,
                      [auth_vars, 'create', 'action', action_name, param])
    mock_method.assert_called_once_with(ANY, action_name,
                                        {'"server-name': 'mcp"'})


def test_create_action_negative():
    """
    negative unit test for create action command
    verifies invalid action command results in error
    """

    action_command = 'invalid_action_command'
    param = '--param="test"'
    runner = CliRunner()
    results = runner.invoke(
        shipyard, [auth_vars, 'create', 'action', action_command, param])
    assert 'Error' in results.output


def test_create_configdocs():
    """test create configdocs with filename"""

    collection = 'design'
    filename = 'shipyard_client/tests/unit/cli/create/sample_yaml/sample.yaml'
    append = 'append'
    runner = CliRunner()
    with patch.object(CreateConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [
            auth_vars, 'create', 'configdocs', collection, '--' + append,
            '--filename=' + filename
        ])
    mock_method.assert_called_once_with(ANY, collection, 'append', ANY)


def test_create_configdocs_directory():
    """test create configdocs with directory"""

    collection = 'design'
    directory = 'shipyard_client/tests/unit/cli/create/sample_yaml'
    append = 'append'
    runner = CliRunner()
    with patch.object(CreateConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [
            auth_vars, 'create', 'configdocs', collection, '--' + append,
            '--directory=' + directory
        ])
    mock_method.assert_called_once_with(ANY, collection, 'append', ANY)


def test_create_configdocs_negative():
    """
    negative unit test for create configdocs command
    verifies invalid filename results in error
    """

    collection = 'design'
    filename = 'invalid.yaml'
    append = 'append'
    runner = CliRunner()
    results = runner.invoke(shipyard, [
        auth_vars, 'create', 'configdocs', collection, '--' + append,
        '--filename=' + filename
    ])
    assert 'Error' in results.output
