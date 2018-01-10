# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-1.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import logging

from click_default_group import DefaultGroup

from .commit import commands as commit
from .control import commands as control
from .create import commands as create
from .describe import commands as describe
from .get import commands as get
from .help import commands as help
from shipyard_client.cli.input_checks import check_control_action, check_id


@click.group(cls=DefaultGroup, default='shipyard_default')
# Shipyard Command Options
@click.option(
    '--context-marker',
    'context_marker',
    help='Specifies a UUID (8-4-4-4-12 format) that will be used to correlate'
    ' logs, transactions, etc. in downstream activities triggered by this'
    ' interaction. If not specified, Shipyard will supply a new UUID to serve'
    ' as this marker. (optional)',
    required=False,
    type=click.UUID)
@click.option('--debug/--no-debug', default=False, help='Turn Debug on.')
@click.option(
    '--output-format',
    'output_format',
    required=False,
    type=click.Choice(['format', 'raw', 'cli']),
    default='cli')
# Supported Environment Variables
@click.option('--os-project-domain-name',
              envvar='OS_PROJECT_DOMAIN_NAME',
              required=False,
              default='default')
@click.option('--os-user-domain-name',
              envvar='OS_USER_DOMAIN_NAME',
              required=False,
              default='default')
@click.option('--os-project-name', envvar='OS_PROJECT_NAME', required=False)
@click.option('--os-username', envvar='OS_USERNAME', required=False)
@click.option('--os-password', envvar='OS_PASSWORD', required=False)
# os_auth_url is required for all command except help, please see shipyard def
@click.option(
    '--os-auth-url', envvar='OS_AUTH_URL', required=False)
# Allows context (ctx) to be passed
@click.pass_context
def shipyard(ctx, context_marker, debug, os_project_domain_name,
             os_user_domain_name, os_project_name, os_username, os_password,
             os_auth_url, output_format):
    """
    COMMAND: shipyard \n
    DESCRIPTION: The base shipyard command supports options that determine
    cross-CLI behaviors. These options are positioned immediately following
    the shipyard command. \n
    FORMAT: shipyard [--context-marker=<uuid>] [--os_{various}=<value>]
    [--debug/--no-debug] [--output-format=<json,yaml,raw] <subcommands> \n
    """
    if not ctx.obj:
        ctx.obj = {}

    ctx.obj['DEBUG'] = debug

    # setup logging for the CLI
    # set up root logger
    logger = logging.getLogger('shipyard_cli')

    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logging_handler = logging.StreamHandler()
    logger.addHandler(logging_handler)
    logger.debug('logging for cli initialized')

    auth_vars = {
        'project_domain_name': os_project_domain_name,
        'user_domain_name': os_user_domain_name,
        'project_name': os_project_name,
        'username': os_username,
        'password': os_password,
        'auth_url': os_auth_url
    }

    ctx.obj['API_PARAMETERS'] = {
        'auth_vars': auth_vars,
        'context_marker': str(context_marker) if context_marker else None,
        'debug': debug
    }

    ctx.obj['FORMAT'] = output_format


shipyard.add_command(commit.commit)
shipyard.add_command(control.control)
shipyard.add_command(create.create)
shipyard.add_command(describe.describe)
shipyard.add_command(get.get)
shipyard.add_command(help.help)


# To Invoke Control Commands
# Since control is not a command used in the CLI, the control commands
# pause, unpause, and stop are invoked here.
@shipyard.command(name='shipyard_default', short_help="")
@click.pass_context
@click.argument('action')
@click.argument('target_type', metavar='[TYPE]')
@click.argument('id', required=False)
def control_command(ctx, action, target_type, id):
    """
    For more information on the control commands (pause, unpause, stop), please
    enter 'shipyard control <control command> --help.'
    """

    check_control_action(ctx, action)

    if id:
        check_id(ctx, id)
        ctx.invoke(
            getattr(control, 'control_' + action),
            target_type=target_type,
            id=id)

    else:
        ctx.invoke(
            getattr(control, 'control_' + action), target_type=target_type)
