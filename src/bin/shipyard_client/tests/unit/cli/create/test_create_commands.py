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
    param = '--param="target_nodes=mcp"'
    runner = CliRunner()
    with patch.object(CreateAction, '__init__') as mock_method:
        runner.invoke(shipyard,
                      [auth_vars, 'create', 'action', action_name, param])
    mock_method.assert_called_once_with(ANY, action_name,
                                        {'"target_nodes': 'mcp"'}, False)


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
    filename = 'tests/unit/cli/create/sample_yaml/sample.yaml'
    append = 'append'
    file_list = (filename,)
    runner = CliRunner()
    with patch.object(CreateConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [
            auth_vars, 'create', 'configdocs', collection, '--' + append,
            '--filename=' + filename
        ])
    mock_method.assert_called_once_with(ctx=ANY, collection=collection,
        buffer_mode='append', empty_collection=False, data=ANY,
        filenames=file_list)


def test_create_configdocs_empty():
    """test create configdocs with the --empty-collection flag"""

    collection = 'design'
    filename = 'tests/unit/cli/create/sample_yaml/sample.yaml'
    directory = 'tests/unit/cli/create/sample_yaml'
    runner = CliRunner()
    tests = [
        {
            # replace mode, no file, no data, empty collection
            'kwargs': {
                'buffer_mode': 'replace',
                'empty_collection': True,
                'filenames': [],
                'data': ""
            },
            'args': [
                '--replace',
                '--empty-collection',
            ],
        },
        {
            # Append mode, no file, no data, empty collection
            'kwargs': {
                'buffer_mode': 'append',
                'empty_collection': True,
                'filenames': [],
                'data': ""
            },
            'args': [
                '--append',
                '--empty-collection',
            ],
        },
        {
            # No buffer mode specified, empty collection
            'kwargs': {
                'buffer_mode': None,
                'empty_collection': True,
                'filenames': [],
                'data': ""
            },
            'args': [
                '--empty-collection',
            ],
        },
        {
            # Filename should be ignored and not passed, empty collection
            'kwargs': {
                'buffer_mode': None,
                'empty_collection': True,
                'filenames': [],
                'data': ""
            },
            'args': [
                '--empty-collection',
                '--filename={}'.format(filename)
            ],
        },
        {
            # Directory should be ignored and not passed, empty collection
            'kwargs': {
                'buffer_mode': None,
                'empty_collection': True,
                'filenames': [],
                'data': ""
            },
            'args': [
                '--empty-collection',
                '--directory={}'.format(directory)
            ],
        },
    ]

    for tc in tests:
        with patch.object(CreateConfigdocs, '__init__') as mock_method:
            runner.invoke(shipyard, [
                auth_vars, 'create', 'configdocs', collection, *tc['args']
            ])

        mock_method.assert_called_once_with(ctx=ANY, collection=collection,
            **tc['kwargs'])


def test_create_configdocs_directory():
    """test create configdocs with directory"""

    collection = 'design'
    directory = 'tests/unit/cli/create/sample_yaml'
    append = 'append'
    runner = CliRunner()
    with patch.object(CreateConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [
            auth_vars, 'create', 'configdocs', collection, '--' + append,
            '--directory=' + directory
        ])
    # TODO(bryan-strassner) Make this test useful to show directory parsing
    #     happened.
    mock_method.assert_called_once_with(ctx=ANY, collection=collection,
        buffer_mode='append', empty_collection=False, data=ANY,
        filenames=ANY)


def test_create_configdocs_directory_empty():
    """test create configdocs with empty directory"""

    collection = 'design'
    dir1 = 'tests/unit/cli/create/no_yaml_dir/'
    runner = CliRunner()

    with patch.object(CreateConfigdocs, 'invoke_and_return_resp') as _method:
        result = runner.invoke(shipyard, [
            auth_vars, 'create', 'configdocs', collection,
            '--directory=' + dir1
        ])
    _method.assert_not_called()
    # verify the error message
    assert  b'directory does not contain any YAML files' in result.stderr_bytes

def test_create_configdocs_multi_directory():
    """test create configdocs with multiple directories"""

    collection = 'design'
    dir1 = 'tests/unit/cli/create/sample_yaml/'
    dir2 = 'tests/unit/cli/create/sample_yaml0/'
    append = 'append'
    runner = CliRunner()
    with patch.object(CreateConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [
            auth_vars, 'create', 'configdocs', collection, '--' + append,
            '--directory=' + dir1, '--directory=' + dir2
        ])
    # TODO(bryan-strassner) Make this test useful to show multiple directories
    #     were actually traversed.
    mock_method.assert_called_once_with(ctx=ANY, collection=collection,
        buffer_mode='append', empty_collection=False, data=ANY,
        filenames=ANY)


def test_create_configdocs_multi_directory_recurse():
    """test create configdocs with multiple directories recursively"""

    collection = 'design'
    dir1 = 'tests/unit/cli/create/sample_yaml/'
    dir2 = 'tests/unit/cli/create/sample_yaml0/'
    append = 'append'
    runner = CliRunner()
    with patch.object(CreateConfigdocs, '__init__') as mock_method:
        runner.invoke(shipyard, [
            auth_vars, 'create', 'configdocs', collection, '--' + append,
            '--directory=' + dir1, '--directory=' + dir2, '--recurse'
        ])
    # TODO(bryan-strassner) Make this test useful to show multiple directories
    #     were actually traversed and recursed.
    mock_method.assert_called_once_with(ctx=ANY, collection=collection,
        buffer_mode='append', empty_collection=False, data=ANY,
        filenames=ANY)


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
