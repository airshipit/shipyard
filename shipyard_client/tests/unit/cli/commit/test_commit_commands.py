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

from shipyard_client.cli.commit.actions import CommitConfigdocs
from shipyard_client.cli.commands import shipyard

auth_vars = ('--os-project-domain-name=OS_PROJECT_DOMAIN_NAME_test '
             '--os-user-domain-name=OS_USER_DOMAIN_NAME_test '
             '--os-project-name=OS_PROJECT_NAME_test '
             '--os-username=OS_USERNAME_test '
             '--os-password=OS_PASSWORD_test '
             '--os-auth-url=OS_AUTH_URL_test')


def test_commit_configdocs(*args):
    """test commit_configdocs"""
    runner = CliRunner()
    with patch.object(CommitConfigdocs, '__init__') as mock_method:
        results = runner.invoke(shipyard, [auth_vars, 'commit', 'configdocs'])
    mock_method.assert_called_once_with(ANY, False)


def test_commit_configdocs_negative():
    """
    negative unit test for commit configdocs command
    verifies invalid argument results in error
    """
    invalid_arg = 'invalid'
    runner = CliRunner()
    results = runner.invoke(shipyard,
                            [auth_vars, 'commit', 'configdocs', invalid_arg])
    assert 'Error' in results.output
