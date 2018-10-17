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
from shipyard_client.cli import cli_format_common
from shipyard_client.cli import format_utils


class CreateAction(CliAction):
    """Action to Create Action"""

    def __init__(self, ctx, action_name, param, allow_intermediate_commits):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            "CreateAction action initialized with action command "
            "%s, parameters %s and allow-intermediate-commits=%s", action_name,
            param, allow_intermediate_commits)
        self.action_name = action_name
        self.param = param
        self.allow_intermediate_commits = allow_intermediate_commits

    def invoke(self):
        """Returns the response from API Client"""
        self.logger.debug("Calling API Client post_actions.")
        return self.get_api_client().post_actions(
            name=self.action_name,
            parameters=self.param,
            allow_intermediate_commits=self.allow_intermediate_commits)

    # Handle 400, 409 with default error handler for cli.
    cli_handled_err_resp_codes = [400, 409]

    # Handle 201 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [201]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a formatted response
            Handles 201 responses
        """
        resp_j = response.json()
        action_list = [resp_j] if resp_j else []
        return cli_format_common.gen_action_table(action_list)


class CreateConfigdocs(CliAction):
    """Action to Create Configdocs"""

    def __init__(self, ctx, collection, buffer_mode, empty_collection, data,
                 filenames):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            "CreateConfigdocs action initialized with collection: %s, "
            "buffer mode: %s, empty collection: %s, data length: %s. "
            "Processed Files:", collection, buffer_mode, empty_collection,
            len(data))
        for file in filenames:
            self.logger.debug(file)
        self.collection = collection
        self.buffer_mode = buffer_mode
        self.empty_collection = empty_collection
        self.data = data

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client post_configdocs.")

        # Only send data payload if not empty_collection
        data_to_send = "" if self.empty_collection else self.data

        return self.get_api_client().post_configdocs(
            collection_id=self.collection,
            buffer_mode=self.buffer_mode,
            empty_collection=self.empty_collection,
            document_data=data_to_send)

    # Handle 409 with default error handler for cli.
    cli_handled_err_resp_codes = [409]

    # Handle 201 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [201]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a formatted response
            Handles 201 responses
        """
        outfmt_string = "Configuration documents added.\n{}"
        return outfmt_string.format(
            format_utils.cli_format_status_handler(response))
