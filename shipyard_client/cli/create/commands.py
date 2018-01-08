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

# Create command

import click
import os
import yaml

from shipyard_client.cli.create.actions import CreateAction, CreateConfigdocs
from shipyard_client.cli.input_checks import check_action_command, \
    check_reformat_parameter


@click.group()
@click.pass_context
def create(ctx):
    """
    Create configdocs or an action. \n
    For more information on create commands
    please enter the create command followed by '--help' \n
    Example: shipyard create action --help
    """


DESC_ACTION = """
    COMMAND: action \n
    DESCRIPTION: Invokes the specified workflow through Shipyard. Returns the
    id of the action invoked so that it can be queried subsequently. \n
    FORMAT: shipyard create action <action command> --param=<parameter>
    (repeatable) \n
    EXAMPLE: shipyard create action redeploy_server --param="server-name=mcp"
"""

SHORT_DESC_ACTION = (
    "Invokes the specified workflow through Shipyard. Returns "
    "the id of the action invoked so that it can be queried "
    "subsequently.")


@create.command(name='action', help=DESC_ACTION, short_help=SHORT_DESC_ACTION)
@click.argument('action_name')
@click.option(
    '--param',
    multiple=True,
    help="A parameter to be provided to the action being invoked.(Repeatable)")
@click.pass_context
def create_action(ctx, action_name, param):
    check_action_command(ctx, action_name)

    if not param and action_name is 'redeploy_server':
        ctx.fail('At least one parameter must be specified using '
                 '--param="<parameter>" with action redeploy_server')
    else:
        param = check_reformat_parameter(ctx, param)
        click.echo(
            CreateAction(ctx, action_name, param).invoke_and_return_resp())


DESC_CONFIGDOCS = """
COMMAND: configdocs \n
DESCRIPTION: Load documents into the Shipyard Buffer. \n
FORMAT: shipyard create configdocs <collection> [--append | --replace]
[--filename=<filename> (repeatable) | --directory=<directory] \n
EXAMPLE: shipyard create configdocs design --append
--filename=site_design.yaml
"""

SHORT_DESC_CONFIGDOCS = "Load documents into the Shipyard Buffer."


@create.command(
    name='configdocs', help=DESC_CONFIGDOCS, short_help=SHORT_DESC_CONFIGDOCS)
@click.argument('collection')
@click.option(
    '--append',
    flag_value=True,
    help='Add the collection to the Shipyard Buffer. ')
@click.option(
    '--replace',
    flag_value=True,
    help='Clear the Shipyard Buffer and replace it with the specified '
    'contents. ')
@click.option(
    '--filename',
    multiple=True,
    type=click.Path(exists=True),
    help='The file name to use as the contents of the collection. '
    '(Repeatable). ')
@click.option(
    '--directory',
    type=click.Path(exists=True),
    help='A directory containing documents that will be joined and loaded as '
    'a collection.')
@click.pass_context
def create_configdocs(ctx, collection, filename, directory, append, replace):

    if (append and replace):
        ctx.fail('Either append or replace may be selected but not both')
    if (not filename and not directory) or (filename and directory):
        ctx.fail('Please specify one or more filenames using '
                 '--filename="<filename>" OR a directory using '
                 '--directory="<directory>"')
    if append:
        create_buffer = 'append'
    elif replace:
        create_buffer = 'replace'
    else:
        create_buffer = None

    if directory:
        filename += tuple(
            [os.path.join(directory, each) for each in os.listdir(directory)
             if each.endswith('.yaml')])
        if filename is None:
            ctx.fail('The directory does not contain any YAML files. Please '
                     'enter one or more YAML files or a directory that '
                     'contains one or more YAML files.')
    docs = []

    for file in filename:
        with open(file, 'r') as stream:
            if file.endswith(".yaml"):
                try:
                    docs += list(yaml.safe_load_all(stream))
                except yaml.YAMLError as exc:
                    ctx.fail('YAML file {} is invalid because {}'
                             .format(file, exc))
            else:
                ctx.fail('The file {} is not a YAML file.  Please enter '
                         'only YAML files.'.format(file))

    data = yaml.safe_dump_all(docs)

    click.echo(
        CreateConfigdocs(ctx, collection, create_buffer, data)
        .invoke_and_return_resp())
