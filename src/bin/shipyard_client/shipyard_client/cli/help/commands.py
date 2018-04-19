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

# help command

import click

from shipyard_client.cli.help.output import actions, configdocs, default, logs


@click.group()
def help():
    """Shipyard Help Command"""
    pass


@help.command(name='help')
@click.argument('topic', required=False)
@click.pass_context
def help(ctx, topic=None):
    """
    Display detailed information on topics. \n
    COMMAND: help \n
    DESCRIPTION: Provides topical help for Shipyard. Note that --help will
    provide more specific command help. \n
    FORMAT: shipyard help <topic> \n
    EXAMPLE: shipyard help configdocs \n
    """

    if topic is None:
        click.echo(default())
    elif topic == 'actions':
        click.echo(actions())
    elif topic == 'configdocs':
        click.echo(configdocs())
    elif topic == 'logs':
        click.echo(logs())
    else:
        ctx.fail("Invalid topic. Run command 'shipyard help' for a list of "
                 " available topics.")
