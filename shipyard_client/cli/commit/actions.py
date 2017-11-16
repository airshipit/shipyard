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

from shipyard_client.cli.action import CliAction
from shipyard_client.cli import format_utils


class CommitConfigdocs(CliAction):
    """Actions to Commit Configdocs"""

    def __init__(self, ctx, force):
        """Sets parameters."""
        super().__init__(ctx)
        self.force = force
        self.logger.debug("CommitConfigdocs action initialized with force=%s",
                          force)

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client commit_configdocs.")
        return self.get_api_client().commit_configdocs(force=self.force)

    # Handle 400, 409 with default error handler for cli.
    cli_handled_err_resp_codes = [400, 409]

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a formatted response
            Handles 200 responses
        """
        outfmt_string = "Configuration documents committed.\n{}"
        return outfmt_string.format(
            format_utils.cli_format_status_handler(response)
        )
