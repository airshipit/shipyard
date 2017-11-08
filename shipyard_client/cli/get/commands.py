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

# Get command

import click

from shipyard_client.cli.get.actions import GetActions
from shipyard_client.cli.get.actions import GetConfigdocs
from shipyard_client.cli.get.actions import GetRenderedConfigdocs


@click.group()
@click.pass_context
def get(ctx):
    """
    Get the actions, confidocs, or renderedconfigdocs. \n
    For more information on get commands
    please enter the get command followed by '--help' \n
    Example: shipyard get actions --help
    """


DESC_ACTIONS = """
COMMAND: actions \n
DESCRIPTION: Lists the actions that have been invoked. \n
FORMAT: shipyard get actions \n
EXAMPLE: shipyard get actions
"""

SHORT_DESC_ACTIONS = "Lists the actions that have been invoked."


@get.command(name='actions', help=DESC_ACTIONS, short_help=SHORT_DESC_ACTIONS)
@click.pass_context
def get_actions(ctx):

    click.echo(GetActions(ctx).invoke_and_return_resp())


DESC_CONFIGDOCS = """
COMMAND: configdocs \n
DESCRIPTION: Retrieve documents loaded into Shipyard, either committed or
from the Shipyard Buffer. \n
FORMAT: shipyard get configdocs <collection> [--committed | --buffer] \n
EXAMPLE: shipyard get configdocs design
"""

SHORT_DESC_CONFIGDOCS = ("Retrieve documents loaded into Shipyard, either "
                         "committed or from the Shipyard Buffer.")


@get.command(
    name='configdocs', help=DESC_CONFIGDOCS, short_help=SHORT_DESC_CONFIGDOCS)
@click.argument('collection')
@click.option(
    '--committed',
    '-c',
    flag_value='committed',
    help='Retrieve the documents that have last been committed for this '
    'collection')
@click.option(
    '--buffer',
    '-b',
    flag_value='buffer',
    help='Retrive the documents that have been loaded into Shipyard since the '
    'prior commit. If no documents have been loaded into the buffer for this '
    'collection, this will return an empty response (default)')
@click.pass_context
def get_configdocs(ctx, collection, buffer, committed):

    if buffer and committed:
        ctx.fail(
            'You must choose whether to retrive the committed OR from the '
            'Shipyard Buffer with --committed or --buffer. ')

    if (not buffer and not committed) or buffer:
        version = 'buffer'

    if committed:
        version = 'committed'

    click.echo(
        GetConfigdocs(ctx, collection, version).invoke_and_return_resp())


DESC_RENDEREDCONFIGDOCS = """
COMMAND: renderedconfigdocs \n
DESCRIPTION: Retrieve the rendered version of documents loaded into
Shipyard. Rendered documents are the "final" version of the documents after
applying Deckhand layering and substitution. \n
FORMAT: shipyard get renderedconfigdocs [--committed | --buffer] \n
EXAMPLE: shipyard get renderedconfigdocs
"""

SHORT_DESC_RENDEREDCONFIGDOCS = (
    "Retrieve the rendered version of documents "
    "loaded into Shipyard. Rendered documents are "
    "the 'final' version of the documents after "
    "applying Deckhand layering and substitution.")


@get.command(
    name='renderedconfigdocs',
    help=DESC_RENDEREDCONFIGDOCS,
    short_help=SHORT_DESC_RENDEREDCONFIGDOCS)
@click.option(
    '--committed',
    '-c',
    flag_value='committed',
    help='Retrieve the documents that have last been committed.')
@click.option(
    '--buffer',
    '-b',
    flag_value='buffer',
    help='Retrieve the documents that have been loaded into Shipyard since the'
    ' prior commit. (default)')
@click.pass_context
def get_renderedconfigdocs(ctx, buffer, committed):

    if buffer and committed:
        ctx.fail(
            'You must choose whether to retrive the committed documents OR the'
            ' docutments in the Shipyard Buffer with --committed or --buffer.')

    if committed:
        version = 'committed'

    else:
        version = 'buffer'

    click.echo(GetRenderedConfigdocs(ctx, version).invoke_and_return_resp())
