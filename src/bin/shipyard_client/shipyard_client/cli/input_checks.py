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
"""CLI value checks invoked from commands"""
import arrow
from arrow.parser import ParserError


def check_action_command(ctx, action_command):
    """Verifies the action command is valid"""
    if action_command not in ['deploy_site', 'update_site', 'redeploy_server']:
        ctx.fail('Invalid action command.  The action commands available are '
                 'deploy_site, update_site, and redeploy_server.')


def check_control_action(ctx, action):
    """Verifies the control action is valid"""
    if action not in ['pause', 'unpause', 'stop']:
        ctx.fail('Invalid action.  Please enter pause, unpause, or stop.')


def check_id(ctx, action_id):
    """Verifies a ULID id is in a valid format"""
    if action_id is None:
        ctx.fail('Invalid ID. None is not a valid action ID.')
    if len(action_id) != 26:
        ctx.fail('Invalid ID. ID can only be 26 characters.')
    if not action_id.isalnum():
        ctx.fail('Invalid ID. ID can only contain letters and numbers.')


def check_workflow_id(ctx, workflow_id):
    """Verifies that a workflow id matches the desired format"""
    if workflow_id is None:
        ctx.fail('Invalid ID. None is not a valid workflow ID.')
    if '__' not in workflow_id:
        ctx.fail('Invalid ID. The ID must cotain a double underscore '
                 'separating the workflow name from the execution date')
    input_date_string = workflow_id.split('__')[1]
    date_format_ok = True
    try:
        parsed_dt = arrow.get(input_date_string)
        if input_date_string != parsed_dt.format('YYYY-MM-DDTHH:mm:ss.SSSSSS'):
            date_format_ok = False
    except ParserError:
        date_format_ok = False

    if not date_format_ok:
        ctx.fail('Invalid ID. The date portion of the ID must conform to '
                 'YYYY-MM-DDTHH:mm:ss.SSSSSS')


def check_reformat_parameter(ctx, param):
    """Checks for <name>=<value> format"""
    param_dictionary = {}
    try:
        for p in param:
            values = p.split('=')
            param_dictionary[values[0]] = values[1]
    except Exception:
        ctx.fail(
            "Invalid parameter or parameter format for " + p +
            ".  Please utilize the format: <parameter name>=<parameter value>")
    return param_dictionary


def check_reformat_versions(ctx, buffer, committed, last_site_action,
                            successful_site_action):
    """Checks and reformat version"""
    versions = []

    if buffer:
        versions.append('buffer')
    if committed:
        versions.append('committed')
    if last_site_action:
        versions.append('last_site_action')
    if successful_site_action:
        versions.append('successful_site_action')

    if len(versions) == 0:
        return ['committed', 'buffer']

    elif len(versions) == 2:
        return versions

    else:
        ctx.fail(
            "Invalid input. User must either\n"
            "1. Pass in 0 versions, in which case --buffer and --committed "
            "versions are assumed\n"
            "2. Pass in 2 valid versions for comparison\n\n"
            "Valid versions are '--buffer', '--committed', "
            "'--last-site-action' and '--successful-site-action'")
