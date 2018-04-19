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

from shipyard_client.cli.control.actions import Control
from shipyard_client.cli.commands import shipyard

auth_vars = ('--os-project-domain-name=OS_PROJECT_DOMAIN_NAME_test '
             '--os-user-domain-name=OS_USER_DOMAIN_NAME_test '
             '--os-project-name=OS_PROJECT_NAME_test '
             '--os-username=OS_USERNAME_test '
             '--os-password=OS_PASSWORD_test '
             '--os-auth-url=OS_AUTH_URL_test')


def test_control_pause(*args):
    """check that control_pause works for both type & id, or qaulified name"""
    target_type = 'action'
    id = '01BTG32JW87G0YKA1K29TKNAFX'
    runner = CliRunner()
    with patch.object(Control, '__init__') as mock_method:
        results = runner.invoke(shipyard,
                                [auth_vars, 'pause', target_type, id])
    mock_method.assert_called_once_with(ANY, 'pause', id)

    qualified_name = target_type + "/" + id
    with patch.object(Control, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'pause', qualified_name])
    mock_method.assert_called_once_with(ANY, 'pause', id)


def test_control_pause_negative(*args):
    """
    negative unit test for control pause command
    verifies invalid id and qualified name results in error
    """
    target_type = 'action'
    id = 'invalid id'
    runner = CliRunner()
    results = runner.invoke(shipyard, [auth_vars, 'pause', target_type, id])
    assert 'Error' in results.output

    qualified_name = 'invalid qualified name'
    results = runner.invoke(shipyard, [auth_vars, 'pause', qualified_name])
    assert 'Error' in results.output


def test_control_unpause(*args):
    """
    check that control_unpause works for both type & id, or qaulified name
    """
    target_type = 'action'
    id = '01BTG32JW87G0YKA1K29TKNAFX'
    runner = CliRunner()
    with patch.object(Control, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'unpause', target_type, id])
    mock_method.assert_called_once_with(ANY, 'unpause', id)

    qualified_name = target_type + "/" + id
    with patch.object(Control, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'unpause', qualified_name])
    mock_method.assert_called_once_with(ANY, 'unpause', id)


def test_control_unpause_negative(*args):
    """
    negative unit test for control unpause command
    verifies invalid id and qualified name results in error
    """

    target_type = 'action'
    id = 'invalid id'
    runner = CliRunner()
    results = runner.invoke(shipyard, [auth_vars, 'unpause', target_type, id])
    assert 'Error' in results.output

    qualified_name = 'invalid qualified name'
    results = runner.invoke(shipyard, [auth_vars, 'unpause', qualified_name])
    assert 'Error' in results.output


def test_control_stop(*args):
    """check that control_stop works for both type & id, or qaulified name"""

    target_type = 'action'
    id = '01BTG32JW87G0YKA1K29TKNAFX'
    runner = CliRunner()
    with patch.object(Control, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'stop', target_type, id])
    mock_method.assert_called_once_with(ANY, 'stop', id)

    qualified_name = target_type + "/" + id
    with patch.object(Control, '__init__') as mock_method:
        runner.invoke(shipyard, [auth_vars, 'stop', qualified_name])
    mock_method.assert_called_once_with(ANY, 'stop', id)


def test_control_stop_negative(*args):
    """
    negative unit test for control stop command
    verifies invalid id and qualified name results in error
    """
    target_type = 'action'
    id = 'invalid id'
    runner = CliRunner()
    results = runner.invoke(shipyard, [auth_vars, 'stop', target_type, id])
    assert 'Error' in results.output

    qualified_name = 'invalid qualified name'
    results = runner.invoke(shipyard, [auth_vars, 'stop', qualified_name])
    assert 'Error' in results.output
