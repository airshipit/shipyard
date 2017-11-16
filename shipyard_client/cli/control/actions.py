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


class Control(CliAction):
    """Action to Pause Process"""

    def __init__(self, ctx, control_verb, action_id):
        """Sets parameters."""
        super().__init__(ctx)
        self.action_id = action_id
        self.control_verb = control_verb
        self.logger.debug("ControlPause action initialized")

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client post_control_action.")
        return self.get_api_client().post_control_action(
            action_id=self.action_id,
            control_verb=self.control_verb
        )

    # Handle 400, 409 with default error handler for cli.
    cli_handled_err_resp_codes = [400, 409]

    # Handle 202 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [202]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a formatted response
            Handles 202 responses
        """
        return "{} successfully submitted for action {}".format(
            self.control_verb, self.action_id)
