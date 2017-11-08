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

# Commit command

import click

from shipyard_client.cli.commit.actions import CommitConfigdocs


@click.group()
@click.pass_context
def commit(ctx):
    """
    Commits confidocs. \n
    For more information on commit commands
    please enter the commit command followed by '--help' \n
    Example: shipyard commit configdocs --help
    """


DESC_CONFIGDOCS = """
COMMAND: configdocs \n
DESCRIPTION: Attempts to commit the Shipyard Buffer documents, first
invoking validation by downstream components. \n
FORMAT: shipyard commit configdocs [--force] \n
EXAMPLE: shipyard commit configdocs
"""

SHORT_DESC_CONFIGDOCS = ("Attempts to commit the Shipyard Buffer documents, "
                         "first invoking validation by downstream components.")


@commit.command(
    name='configdocs', help=DESC_CONFIGDOCS, short_help=SHORT_DESC_CONFIGDOCS)
@click.option(
    '--force',
    '-f',
    flag_value=True,
    help='Force the commit to occur, even if validations fail.')
@click.pass_context
def commit_configdocs(ctx, force):
    click.echo(CommitConfigdocs(ctx, force).invoke_and_return_resp())
