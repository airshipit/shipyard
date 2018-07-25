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
from unittest.mock import patch, ANY

from click.testing import CliRunner

from shipyard_client.cli.get.actions import (
    GetActions, GetConfigdocs, GetConfigdocsStatus, GetRenderedConfigdocs,
    GetWorkflows)
from shipyard_client.cli.commands import shipyard

auth_vars = ('--os-project-domain-name=OS_PROJECT_DOMAIN_NAME_test '
             '--os-user-domain-name=OS_USER_DOMAIN_NAME_test '
             '--os-project-name=OS_PROJECT_NAME_test '
             '--os-username=OS_USERNAME_test '
             '--os-password=OS_PASSWORD_test '
             '--os-auth-url=OS_AUTH_URL_test')


def test_get_actions(*args):
    """test get_actions"""

    runner = CliRunner()
    with patch.object(GetActions, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'get', 'actions'])
    mock_method.assert_called_once_with(ANY)


def test_get_actions_negative(*args):
    """Negative unit test for get actions command.

    Verifies invalid argument results in error.
    """

    invalid_arg = 'invalid'
    runner = CliRunner()
    results = runner.invoke(shipyard,
                            [auth_vars, 'get', 'actions', invalid_arg])
    assert 'Error' in results.output


def test_get_configdocs_with_passing_collection(*args):
    """test get_configdocs"""

    runner = CliRunner()
    # verify GetConfigdocs is called when a collection is entered
    with patch.object(GetConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'get', 'configdocs',
                                 '--collection=design'])
    mock_method.assert_called_once_with(ANY, 'design', 'buffer')


def test_get_configdocs_without_passing_collection(*args):
    # verify GetConfigdocsStatus is called when no arguments are entered
    runner = CliRunner()
    with patch.object(GetConfigdocsStatus, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'get', 'configdocs'])
    mock_method.assert_called_once_with(ANY, ['committed', 'buffer'])


def test_get_configdocs_negative(*args):
    """Negative unit test for get configdocs command.

    Verifies invalid argument results in error.
    """

    collection = 'design'
    invalid_arg = 'invalid'
    runner = CliRunner()
    results = runner.invoke(
        shipyard, [auth_vars, 'get', 'configdocs', collection, invalid_arg])
    assert 'Error' in results.output


def test_get_renderedconfigdocs(*args):
    """test get_rendereddocs"""
    runner = CliRunner()
    with patch.object(GetRenderedConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'get', 'renderedconfigdocs'])
    mock_method.assert_called_once_with(ANY, 'buffer')


def test_get_renderedconfigdocs_negative(*args):
    """Negative unit test for get renderedconfigdocs command.

    Verifies invalid argument results in error.
    """

    invalid_arg = 'invalid'
    runner = CliRunner()
    results = runner.invoke(
        shipyard, [auth_vars, 'get', 'renderedconfigdocs', invalid_arg])
    assert 'Error' in results.output


def test_get_workflows(*args):
    """test get_workflows"""

    runner = CliRunner()
    with patch.object(GetWorkflows, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'get', 'workflows'])
    mock_method.assert_called_once_with(ANY, None)

    since_val = '2017-01-01T12:34:56Z'
    since_arg = '--since={}'.format(since_val)
    with patch.object(GetWorkflows, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'get', 'workflows', since_arg])
    mock_method.assert_called_once_with(ANY, since_val)


def test_get_workflows_negative(*args):
    """Negative unit test for get workflows command"""

    invalid_arg = 'invalid_date'
    runner = CliRunner()
    results = runner.invoke(shipyard,
                            [auth_vars, 'get', 'workflows', invalid_arg])
    assert 'Error' in results.output
