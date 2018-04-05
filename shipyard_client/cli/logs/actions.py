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

from shipyard_client.cli.action import CliAction
from shipyard_client.cli import format_utils


class LogsStep(CliAction):
    """Action to Retrieve Logs for a particular Step"""

    def __init__(self, ctx, action_id, step_id, try_number=None):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            "LogsStep action initialized with action_id=%s and step_id=%s",
            action_id, step_id)
        self.action_id = action_id
        self.step_id = step_id
        self.try_number = try_number

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_step_log.")
        return self.get_api_client().get_step_log(
            action_id=self.action_id,
            step_id=self.step_id,
            try_number=self.try_number)

    # Handle 404 with default error handler for cli.
    cli_handled_err_resp_codes = [404]

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        Effectively passes through the logs received.
        :param response: a requests response object
        :returns: a string representing a CLI appropriate response
            Handles 200 responses
        """
        return format_utils.raw_format_response_handler(response)
