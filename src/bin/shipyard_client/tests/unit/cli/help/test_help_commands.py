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
import os

from click.testing import CliRunner
import yaml

from shipyard_client.cli.help.commands import help

def _get_actions_list():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    a_path = dir_path.split('src/bin')[0] + "src/bin/supported_actions.yaml"
    with open(a_path, 'r') as stream:
        try:
            action_list = yaml.safe_load(stream)['actions']
            if not action_list:
                raise FileNotFoundError("Action list is empty")
        except Exception as e:
            print(e)
            print("This test requires that the file at '{}' is a valid yaml "
                    "file containing a list of action names at a key of "
                    "'actions'".format(a_path))
            assert False
    return action_list


def test_help():
    """test help with all options"""

    runner = CliRunner()
    result = runner.invoke(help)
    assert 'THE SHIPYARD COMMAND' in result.output

    topic = 'actions'
    result = runner.invoke(help, [topic])
    assert 'ACTIONS' in result.output
    actions = _get_actions_list()
    for action in actions:
        # Assert that actions each have headers
        assert "\n{}\n".format(action) in result.output

    topic = 'configdocs'
    result = runner.invoke(help, [topic])
    assert 'CONFIGDOCS' in result.output


def test_help_negative():
    """
    negative unit test for help command
    verfies invalid topic results in error
    """

    invalid_topic = 'invalid'
    runner = CliRunner()
    result = runner.invoke(help, [invalid_topic])
    assert 'Error' in result.output
