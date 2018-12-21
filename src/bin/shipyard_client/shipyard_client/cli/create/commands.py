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
    (repeatable) [--allow-intermediate-commits] \n
    EXAMPLE: shipyard create action redeploy_server --param="target_nodes=mcp"
             shipyard create action update_site --param="continue-on-fail=true"
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
@click.option(
    '--allow-intermediate-commits',
    'allow_intermediate_commits',
    is_flag=True,
    help="Allow site action to go through even though there are prior commits "
    "that have not been used as part of a site action.")
@click.pass_context
def create_action(ctx, action_name, param, allow_intermediate_commits=False):
    check_action_command(ctx, action_name)

    if not param and action_name is 'redeploy_server':
        ctx.fail('At least one parameter must be specified using '
                 '--param="<parameter>" with action redeploy_server')
    else:
        param = check_reformat_parameter(ctx, param)
        click.echo(
            CreateAction(ctx,
                         action_name,
                         param,
                         allow_intermediate_commits).invoke_and_return_resp())


DESC_CONFIGDOCS = """
COMMAND: configdocs \n
DESCRIPTION: Load documents into the Shipyard Buffer. \n
FORMAT: shipyard create configdocs <collection> [--append | --replace]
[--empty-collection]
[--filename=<filename> (repeatable) | --directory=<directory>] (repeatable)
 --recurse\n
EXAMPLE: shipyard create configdocs design --append
--filename=site_design.yaml
"""

SHORT_DESC_CONFIGDOCS = "Load documents into the Shipyard Buffer."


@create.command(
    name='configdocs', help=DESC_CONFIGDOCS, short_help=SHORT_DESC_CONFIGDOCS)
@click.argument('collection')
@click.option(
    '--append',
    is_flag=True,
    help='Add the collection to the Shipyard Buffer. ')
@click.option(
    '--replace',
    is_flag=True,
    help='Clear the Shipyard Buffer and replace it with the specified '
    'contents. ')
@click.option(
    '--filename',
    'filenames',
    multiple=True,
    type=click.Path(exists=True),
    help='The file name to use as the contents of the collection. '
    '(Repeatable). ')
@click.option(
    '--directory',
    multiple=True,
    type=click.Path(exists=True),
    help='A directory containing documents that will be joined and loaded as '
    'a collection. (Repeatable).')
@click.option(
    '--recurse',
    is_flag=True,
    help='Recursively search through directories for yaml files.'
)
# The --empty-collection flag is explicit to prevent a user from accidentally
# loading an empty file and deleting things. This requires the user to clearly
# state their intention.
@click.option(
    '--empty-collection',
    is_flag=True,
    help='Creates a version of the specified collection with no contents. '
    'This option is the method by which a collection can be effectively '
    'deleted. Any file and directory parameters will be ignored if this '
    'option is used.'
)
@click.pass_context
def create_configdocs(ctx, collection, filenames, directory, append, replace,
                      recurse, empty_collection):
    if (append and replace):
        ctx.fail('Either append or replace may be selected but not both')

    if append:
        buffer_mode = 'append'
    elif replace:
        buffer_mode = 'replace'
    else:
        buffer_mode = None

    if empty_collection:
        # Use an empty string as the document payload, and indicate no files.
        data = ""
        filenames = []
    else:
        # Validate that appropriate file/directory params were specified.
        if (not filenames and not directory) or (filenames and directory):
            ctx.fail('Please specify one or more filenames using '
                     '--filename="<filename>" OR one or more directories '
                     'using --directory="<directory>"')
        # Scan and parse the input directories and files
        if directory:
            for _dir in directory:
                if recurse:
                    for path, dirs, files in os.walk(_dir):
                        filenames += tuple([
                            os.path.join(path, name) for name in files
                            if is_yaml(name)
                        ])
                else:
                    filenames += tuple([
                        os.path.join(_dir, each) for each in os.listdir(_dir)
                        if is_yaml(each)
                    ])

            if not filenames:
                # None or empty list should raise this error
                ctx.fail('The directory does not contain any YAML files. '
                         'Please enter one or more YAML files or a '
                         'directory that contains one or more YAML files.')

        docs = []
        for _file in filenames:
            with open(_file, 'r') as stream:
                if is_yaml(_file):
                    try:
                        docs += list(yaml.safe_load_all(stream))
                    except yaml.YAMLError as exc:
                        ctx.fail('YAML file {} is invalid because {}'.format(
                            _file, exc))
                else:
                    ctx.fail('The file {} is not a YAML file.  Please enter '
                             'only YAML files.'.format(_file))

        data = yaml.safe_dump_all(docs)

    click.echo(
        CreateConfigdocs(
            ctx=ctx,
            collection=collection,
            buffer_mode=buffer_mode,
            empty_collection=empty_collection,
            data=data,
            filenames=filenames).invoke_and_return_resp())


def is_yaml(filename):
    """Test if the filename should be regarded as a yaml file"""
    return filename.endswith(".yaml") or filename.endswith(".yml")
