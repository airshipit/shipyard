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
import abc
import logging

from shipyard_client.api_client.client_error import ClientError
from shipyard_client.api_client.client_error import UnauthenticatedClientError
from shipyard_client.api_client.client_error import UnauthorizedClientError
from shipyard_client.api_client.shipyard_api_client import ShipyardClient
from shipyard_client.api_client.shipyardclient_context import \
    ShipyardClientContext
from shipyard_client.cli import format_utils


class AuthValuesError(Exception):
    """Signals a failure in the authentication values provided to an action

    Daignostic parameter is forced since newlines in exception text apparently
    do not print with the exception.
    """
    def __init__(self, *, diagnostic):
        self.diagnostic = diagnostic


class AbstractCliAction(metaclass=abc.ABCMeta):
    """Abstract base class for CLI actions

    Base class to encapsulate the items that must be implemented by
    concrete actions
    """

    @abc.abstractmethod
    def invoke(self):
        """Default invoke for CLI actions

        Descendent classes must override this method to perform the actual
        needed invocation. The expected response from this method is a response
        object or raise an exception.
        """
        pass

    @property
    @abc.abstractmethod
    def cli_handled_err_resp_codes(self):
        """Error response codes

        Descendent classes shadow this for those response codes from invocation
        that should be handled using the format_utils.cli_format_error_handler
        Note that 401, 403 responses are handled prior to this via exception,
        and should not be represented here. e.g.: [400, 409].
        """
        pass

    @property
    @abc.abstractmethod
    def cli_handled_succ_resp_codes(self):
        """Success response codes

        Concrete actions must implement cli_handled_succ_resp_codes to indicate
        the response code that should utilize the overridden
        cli_format_response_handler of the sepecific action
        """
        pass

    @abc.abstractmethod
    def cli_format_response_handler(self, response):
        """Abstract format handler for cli output "good" responses

        Overridden by descendent classes to indicate the specific output format
        when the ation is invoked with a output format of "cli".

        Expected to return the string of the output.

        For those actions that do not have a valid "cli" output, the following
        would be generally appropriate for an implementation of this method to
        return the api client's response:

        return format_utils.formatted_response_handler(response)
        """
        pass


class CliAction(AbstractCliAction):
    """Action base for CliActions"""

    def __init__(self, ctx):
        """Initialize CliAction"""
        self.logger = logging.getLogger('shipyard_cli')
        self.api_parameters = ctx.obj['API_PARAMETERS']
        self.resp_txt = ""
        self.needs_credentials = False
        self.output_format = ctx.obj['FORMAT']

        self.auth_vars = self.api_parameters.get('auth_vars')
        self.context_marker = self.api_parameters.get('context_marker')
        self.debug = self.api_parameters.get('debug')

        self.client_context = ShipyardClientContext(
            self.auth_vars, self.context_marker, self.debug)

    def get_api_client(self):
        """Returns the api client for this action"""
        return ShipyardClient(self.client_context)

    def invoke_and_return_resp(self):
        """Lifecycle method to invoke and return a response

        Calls the invoke method in the child action and returns the formatted
        response.
        """
        self.logger.debug("Invoking: %s", self.__class__.__name__)

        try:
            self.validate_auth_vars()
            self.resp_txt = self.output_formatter(self.invoke())
        except AuthValuesError as ave:
            self.resp_txt = "Error: {}".format(ave.diagnostic)
        except UnauthenticatedClientError:
            self.resp_txt = ("Error: Command requires authentication. "
                             "Check credential values")
        except UnauthorizedClientError:
            self.resp_txt = "Error: Unauthorized to perform this action."
        except ClientError as ex:
            self.resp_txt = "Error: Client Error: {}".format(str(ex))
        except Exception as ex:
            self.resp_txt = (
                "Error: Unable to invoke action due to: {}".format(str(ex)))

        return self.resp_txt

    def output_formatter(self, response):
        """Formats response (Requests library) from api_client

        Dispatches to the appropriate response format handler.
        """
        if self.output_format == 'raw':
            return format_utils.raw_format_response_handler(response)
        elif self.output_format == 'cli':
            if response.status_code in self.cli_handled_err_resp_codes:
                return format_utils.cli_format_error_handler(response)
            elif response.status_code in self.cli_handled_succ_resp_codes:
                return self.cli_format_response_handler(response)
            else:
                self.logger.debug("Unexpected response received")
                return format_utils.cli_format_error_handler(response)
        else:  # assume formatted
            return format_utils.formatted_response_handler(response)

    def validate_auth_vars(self):
        """Checks that the required authorization varible have been entered"""
        required_auth_vars = ['auth_url']
        err_txt = []
        for var in required_auth_vars:
            if self.auth_vars[var] is None:
                err_txt.append(
                    'Missing the required authorization variable: '
                    '--os-{}'.format(var.replace('_', '-')))
        if err_txt:
            for var in self.auth_vars:
                if (self.auth_vars.get(var) is None and
                        var not in required_auth_vars):
                    err_txt.append('- Also not set: --os-{}'.format(
                        var.replace('_', '-')))
            raise AuthValuesError(diagnostic='\n'.join(err_txt))
