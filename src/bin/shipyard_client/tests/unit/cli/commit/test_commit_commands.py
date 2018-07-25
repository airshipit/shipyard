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
from unittest import mock
from unittest.mock import patch, ANY

from click.testing import CliRunner

from shipyard_client.cli.commit.actions import CommitConfigdocs
from shipyard_client.cli.commands import shipyard

auth_vars = ('--os-project-domain-name=OS_PROJECT_DOMAIN_NAME_test '
             '--os-user-domain-name=OS_USER_DOMAIN_NAME_test '
             '--os-project-name=OS_PROJECT_NAME_test '
             '--os-username=OS_USERNAME_test '
             '--os-password=OS_PASSWORD_test '
             '--os-auth-url=OS_AUTH_URL_test')


def test_commit_configdocs(*args):
    """test commit configdocs command"""
    runner = CliRunner()
    with patch.object(CommitConfigdocs, '__init__') as mock_method:
        results = runner.invoke(shipyard, [auth_vars, 'commit', 'configdocs'])
    mock_method.assert_called_once_with(ANY, False, False)


def test_commit_configdocs_options(*args):
    """test commit configdocs command with options"""
    runner = CliRunner()
    options = ['--force', '--dryrun']
    with patch.object(CommitConfigdocs, '__init__') as mock_method:
        for opt in options:
            results = runner.invoke(shipyard, [auth_vars, 'commit',
                                    'configdocs', opt])
    mock_method.assert_has_calls([
        mock.call(ANY, True, False),
        mock.call(ANY, False, True)
    ])


def test_commit_configdocs_negative_invalid_arg():
    """
    negative unit test for commit configdocs command
    verifies invalid argument results in error
    """
    invalid_arg = 'invalid'
    runner = CliRunner()
    results = runner.invoke(shipyard,
                            [auth_vars, 'commit', 'configdocs', invalid_arg])
    assert 'Error' in results.output


def test_commit_configdocs_negative_force_dryrun():
    """
    negative unit test for commit configdocs command
    verifies when force and dryrun are selected, and error occurs
    """
    invalid_arg = 'invalid'
    runner = CliRunner()
    results = runner.invoke(shipyard,
                            [auth_vars, 'commit', 'configdocs', '--force',
                             '--dryrun'])
    assert ('Error: Either force or dryrun may be selected but not both' in
            results.output)
