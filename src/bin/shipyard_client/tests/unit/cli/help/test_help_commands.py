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

from shipyard_client.cli.help.commands import help


def test_help():
    """test help with all options"""

    runner = CliRunner()
    result = runner.invoke(help)
    assert 'THE SHIPYARD COMMAND' in result.output

    topic = 'actions'
    result = runner.invoke(help, [topic])
    assert 'ACTIONS' in result.output

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
