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


def check_action_command(ctx, action_command):
    """verifies the action command is valid"""
    if (action_command != "deploy_site") and (
            action_command != "update_site") and (action_command !=
                                                  "redeploy_server"):
        ctx.fail('Invalid action command.  The action commands available are '
                 'deploy_site, update_site, and redeploy_server.')


def check_control_action(ctx, action):
    """verifies the control action is valid"""
    if (action != 'pause') and (action != 'unpause') and (action != 'stop'):
        ctx.fail('Invalid action.  Please enter pause, unpause, or stop.')


def check_id(ctx, id):
    """verifies the id is valid"""
    if (len(id) != 26):
        ctx.fail('Invalid ID. ID can only be 26 characters.')
    if not id.isalnum():
        ctx.fail('Invalid ID. ID can only contain letters and numbers.')


def validate_auth_vars(self, ctx):
    """ Checks that the required authurization varible have been entered """

    required_auth_vars = ['auth_url']
    auth_vars = self.api_parameters['auth_vars']
    for var in required_auth_vars:
        if auth_vars[var] is None:
            self.resp_txt += (
                'Missing the required authorization variable: ' + var + '\n')
    if self.resp_txt is not "":
        self.resp_txt += ('\nMissing the following additional authorization '
                          'options: ')
        for var in auth_vars:
            if auth_vars[var] is None and var not in required_auth_vars:
                self.resp_txt += '\n--os_' + var
        ctx.fail(self.resp_txt)


def check_reformat_parameter(ctx, param):
    param_dictionary = {}
    try:
        for p in param:
            values = p.split('=')
            param_dictionary[values[0]] = values[1]
    except:
        ctx.fail(
            "Invalid parameter or parameter format for " + p +
            ".  Please utilize the format: <parameter name>=<parameter value>")
    return param_dictionary
