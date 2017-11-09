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

# Base classes for cli actions intended to invoke the api

import logging

from shipyard_client.api_client.shipyard_api_client import ShipyardClient
from shipyard_client.api_client.shipyardclient_context import \
    ShipyardClientContext
from shipyard_client.api_client.client_error import ClientError
from shipyard_client.cli.input_checks import validate_auth_vars


class CliAction(object):
    """Action base for CliActions"""

    def __init__(self, ctx):
        """Sets api_client"""
        self.logger = logging.getLogger('shipyard_cli')
        self.api_parameters = ctx.obj['API_PARAMETERS']
        self.resp_txt = ""
        self.needs_credentials = False

        auth_vars = self.api_parameters['auth_vars']
        context_marker = self.api_parameters['context_marker']
        debug = self.api_parameters['debug']

        validate_auth_vars(ctx, self.api_parameters.get('auth_vars'))

        self.logger.debug("Passing environment varibles to the API client")
        try:
            shipyard_client_context = ShipyardClientContext(
                auth_vars, context_marker, debug)
            self.api_client = ShipyardClient(shipyard_client_context)
        except ClientError as e:
            self.logger.debug("The shipyard Client Context could not be set.")
            ctx.fail('Client Error: %s.' % str(e))

    def invoke_and_return_resp(self):
        """
        calls the invoke method in the approiate actions.py and returns the
        formatted response
        """

        self.logger.debug("Inoking action.")
        env_vars = self.api_parameters['auth_vars']

        try:
            self.invoke()
        except ClientError as e:
            self.resp_txt = "Client Error: %s." % str(e)
        except Exception as e:
            self.resp_txt = "Error: Unable to invoke action because %s." % str(
                e)

        return self.resp_txt

    def invoke(self):
        """Default invoke"""
        self.resp_txt = "Error: Invoke method is not defined for this action."
