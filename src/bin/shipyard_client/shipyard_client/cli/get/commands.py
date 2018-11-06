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
from shipyard_client.cli.get.actions import GetConfigdocsStatus
from shipyard_client.cli.get.actions import GetRenderedConfigdocs
from shipyard_client.cli.get.actions import GetWorkflows
from shipyard_client.cli.get.actions import GetSiteStatuses
from shipyard_client.cli.input_checks import check_reformat_versions


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
COMMAND: configdocs
DESCRIPTION: Retrieve documents loaded into Shipyard, either committed,
last site action, successful site action or from the Shipyard Buffer.
Allows comparison between 2 revisions using valid revision tags.
FORMAT: shipyard get configdocs [--collection=<collection>]
[--committed | --buffer | --last-site-action | --successful-site-action]
EXAMPLE: shipyard get configdocs --colllection=design
"""

SHORT_DESC_CONFIGDOCS = ("Retrieve documents loaded into Shipyard, either "
                         "committed, last site action, successful site action"
                         " or from the Shipyard Buffer. Allows comparison "
                         "between 2 revisions using valid revision tags")


@get.command(
    name='configdocs', help=DESC_CONFIGDOCS, short_help=SHORT_DESC_CONFIGDOCS)
@click.option(
    '--collection',
    help='A collection of document YAMLs')
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
    help='Retrieve the documents that have been loaded into Shipyard since '
    'the prior commit. If no documents have been loaded into the buffer for '
    'this collection, this will return an empty response (default)')
@click.option(
    '--last-site-action',
    '-l',
    flag_value='last_site_action',
    help='Holds the revision information for the most recent site action')
@click.option(
    '--successful-site-action',
    '-s',
    flag_value='successful_site_action',
    help='Holds the revision information for the most recent successfully '
    'executed site action.')
@click.option(
    '--cleartext-secrets',
    '-t',
    help='Returns cleartext secrets in documents',
    is_flag=True)
@click.pass_context
def get_configdocs(ctx, collection, buffer, committed, last_site_action,
                   successful_site_action, cleartext_secrets):
    if collection:
        # Get version
        _version = get_version(ctx, buffer, committed, last_site_action,
                               successful_site_action)

        click.echo(
            GetConfigdocs(ctx, collection, _version,
                          cleartext_secrets).invoke_and_return_resp())

    else:
        compare_versions = check_reformat_versions(ctx,
                                                   buffer,
                                                   committed,
                                                   last_site_action,
                                                   successful_site_action)

        click.echo(
            GetConfigdocsStatus(ctx,
                                compare_versions).invoke_and_return_resp())


DESC_RENDEREDCONFIGDOCS = """
COMMAND: renderedconfigdocs
DESCRIPTION: Retrieve the rendered version of documents loaded into
Shipyard. Rendered documents are the "final" version of the documents after
applying Deckhand layering and substitution.
FORMAT: shipyard get renderedconfigdocs
[--committed | --buffer | --last-site-action | --successful-site-action]
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
@click.option(
    '--last-site-action',
    '-l',
    flag_value='last_site_action',
    help='Holds the revision information for the most recent site action')
@click.option(
    '--successful-site-action',
    '-s',
    flag_value='successful_site_action',
    help='Holds the revision information for the most recent successfully '
    'executed site action.')
@click.pass_context
def get_renderedconfigdocs(ctx, buffer, committed, last_site_action,
                           successful_site_action):
    # Get version
    _version = get_version(ctx, buffer, committed, last_site_action,
                           successful_site_action)

    click.echo(GetRenderedConfigdocs(ctx, _version).invoke_and_return_resp())


DESC_WORKFLOWS = """
COMMAND: workflows \n
DESCRIPTION: Lists the workflows from airflow. \n
FORMAT: shipyard get workflows [since]\n
EXAMPLE: \n
    shipyard get workflows \n
    shipyard get workflows --since=2017-11-09T15:02:18Z
"""

SHORT_DESC_WORKFLOWS = "Lists the workflows from airflow."


@get.command(
    name='workflows', help=DESC_WORKFLOWS, short_help=SHORT_DESC_WORKFLOWS)
@click.option(
    '--since',
    help=('A boundary in the past within which to retrieve results.'
          'Default is 30 days in the past.'))
@click.pass_context
def get_workflows(ctx, since):

    click.echo(GetWorkflows(ctx, since).invoke_and_return_resp())


def get_version(ctx, buffer, committed, last_site_action,
                successful_site_action):

    # Check number of optional site parameters
    # User can only query with 1 of these options
    optional_site_parameters = []

    if buffer:
        optional_site_parameters.append('buffer')
    if committed:
        optional_site_parameters.append('committed')
    if last_site_action:
        optional_site_parameters.append('last_site_action')
    if successful_site_action:
        optional_site_parameters.append('successful_site_action')

    if len(optional_site_parameters) > 1:
        ctx.fail(
            'You may only choose one of the following options:\n'
            '--buffer for the documents in the Shipyard buffer\n'
            '--committed for the last committed revision of the documents\n'
            '--last-site-action for the documents associated with the last '
            'successful or failed site action\n'
            '--successful-site-action for the documents associated with the '
            'last successful site action\n'
            'Site actions are deploy_site, update_site, and update_software')

    elif len(optional_site_parameters) == 1:
        return optional_site_parameters[0]

    else:
        return 'buffer'


DESC_STATUS = """
COMMAND: status
DESCRIPTION: Retrieve statuses of different status types for the site.
Supported status types are nodes-provision-status and machines-power-state. \n
Status type nodes-provision-status will fetch provisioning status for all nodes
and machines-power-state will fetch power state for all baremetal machines
in the site. Supports fetching statuses of multiple types. Without status-type
option, command fetches statuses of all status types. \n
FORMAT: shipyard get site-statuses [--status-type=<status-type>] (repeatable)\n
EXAMPLE: shipyard get status --status-type=nodes-provision-status \
 --status-type=machines-power-state
"""

SHORT_DESC_STATUS = "Retrieve statuses for the site."


@get.command(
    name='site-statuses',
    help=DESC_STATUS,
    short_help=SHORT_DESC_STATUS)
@click.option(
    '--status-type',
    '-s',
    multiple=True,
    help='Fetches statuses of specific status type.(repeatable) \n'
    'Supported status types are: \n'
    'nodes-provision-status \n'
    'machines-power-state')
@click.pass_context
def get_site_statuses(ctx, status_type):

    fltr = ",".join(status_type)
    click.echo(GetSiteStatuses(ctx, fltr).invoke_and_return_resp())
