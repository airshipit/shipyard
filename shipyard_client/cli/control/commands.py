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

# Control command

import click

from shipyard_client.cli.control.actions import Control


@click.group()
@click.pass_context
def control(ctx):
    """
    Pause, unpause, or stop something in progress. \n
    For more information on control commands
    please enter the control command followed by '--help' \n
    Example: shipyard control pause --help
    """


DESC_PAUSE = """
COMMAND: pause \n
DESCRIPTION: Pause something in progress. \n
FORMAT: shipyard pause [<type> <id>] | [<qualified name>] \n
EXAMPLE: shipyard pause action 01BTG32JW87G0YKA1K29TKNAFX | shipyard pause
action/01BTG32JW87G0YKA1K29TKNAFX
"""

SHORT_DESC_PAUSE = "Pause something in progress."


@control.command(name='pause', help=DESC_PAUSE, short_help=SHORT_DESC_PAUSE)
@click.argument(
    'target_type', metavar='[TYPE]', required=True)  # type or qualified name
@click.argument('id', required=False)
@click.pass_context
def control_pause(ctx, target_type, id=None):

    control_handler(ctx, target_type, 'pause', id)


DESC_UNPAUSE = """
COMMAND: unpause \n
DESCRIPTION: Unpause something in progress. \n
FORMAT: shipyard unpause [<type> <id>] | [<qualified name>] \n
EXAMPLE: shipyard unpause action 01BTG32JW87G0YKA1K29TKNAFX | shipyard
unpause action/01BTG32JW87G0YKA1K29TKNAFX
"""

SHORT_DESC_UNPAUSE = "Unpause something in progress."


@control.command(
    name='unpause', help=DESC_UNPAUSE, short_help=SHORT_DESC_UNPAUSE)
@click.argument(
    'target_type', metavar='[TYPE]', required=True)  # type or qualified name
@click.argument('id', required=False)
@click.pass_context
def control_unpause(ctx, target_type, id=None):

    control_handler(ctx, target_type, 'unpause', id)


DESC_STOP = """
COMMAND: stop \n
DESCRIPTION: Stop an executing or paused item. \n
FORMAT: shipyard stop [<type> <id>] | [<qualified name>] \n
EXAMPLE: shipyard stop action 01BTG32JW87G0YKA1K29TKNAFX | shipyard stop
action/01BTG32JW87G0YKA1K29TKNAFX
"""

SHORT_DESC_STOP = "Stop an executing or paused item."


@control.command(name='stop', help=DESC_STOP, short_help=SHORT_DESC_STOP)
@click.argument(
    'target_type', metavar='[TYPE]', required=True)  # type or qualified name
@click.argument('id', required=False)
@click.pass_context
def control_stop(ctx, target_type, id=None):

    control_handler(ctx, target_type, 'stop', id)


def control_handler(ctx, target_type, control_verb, id):
    """
    Handles spliting the qualified_name if needed and passes to actions.py
    """

    # if id is not entered, then qualified name is entered
    if id is None:
        name = target_type.split("/")
        if len(name) == 2:
            target_type, id = name
        else:
            ctx.fail('A type and id must be entered.')

    click.echo(Control(ctx, control_verb, id).invoke_and_return_resp())
