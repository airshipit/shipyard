# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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

# Logs command

import click

from click_default_group import DefaultGroup

from shipyard_client.cli.logs.actions import LogsStep


@click.group(cls=DefaultGroup, default='logs_default_command')
@click.pass_context
def logs(ctx):
    """
    Get the logs of a particular step.
    For more information on logs commands
    please enter the logs command followed by '--help'
    Example: shipyard logs step --help

    FOR NAMESPACE ENTRIES:
        COMMAND: (no sub command)
        DESCRIPTION: Retrieves the logs of the supplied namespaced item.
        FORMAT: shipyard logs <namespace item>
        EXAMPLE: shipyard logs step/01CASSSZT7CP1F0NKHCAJBCJGR/action_xcom
    """


@logs.command('logs_default_command', short_help="")
@click.argument('namespace_item')
@click.pass_context
def logs_default_command(ctx, namespace_item):
    try:
        namespace = namespace_item.split("/")
        if namespace[0] == 'step':
            if len(namespace) == 4:
                ctx.invoke(logs_step,
                           action=namespace[1],
                           step_id=namespace[2],
                           try_number=namespace[3])
            else:
                ctx.invoke(logs_step,
                           action=namespace[1],
                           step_id=namespace[2],
                           try_number=None)
        else:
            raise Exception('Invalid namespaced logs action')
    except Exception:
        ctx.fail("Invalid namespace item. Please utilize the following "
                 "format for the namespace item."
                 "step: step/action_id/step_id")


LOGS_STEP = """
COMMAND: logs step
DESCRIPTION: Retrieves logs for a particular step.
FORMAT: shipyard logs step <step_id> --action=<action_id> --try=<try>
EXAMPLE:
shipyard logs step drydock_validate_site_design
 --action=01C7ECDZF7MC8JEVE8NA8PS764 --try=2
"""

SHORT_LOGS_STEP = ("Retrieve logs for a particular step.")


@logs.command('step', help=LOGS_STEP, short_help=SHORT_LOGS_STEP)
@click.argument('step_id', nargs=1)
@click.option(
    '--action',
    '-a',
    required=True,
    help='The action name for this step')
@click.option(
    '--try',
    '-t',
    'try_number',
    help='The try number that provides the context for this step')
@click.pass_context
def logs_step(ctx, action, step_id, try_number=None):

    click.echo(LogsStep(ctx,
                        action,
                        step_id,
                        try_number).invoke_and_return_resp())
