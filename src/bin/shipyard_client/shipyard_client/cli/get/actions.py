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


class GetActions(CliAction):
    """Action to Get Actions"""

    def __init__(self, ctx):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug("GetActions action initialized.")

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_actions.")
        return self.get_api_client().get_actions()

    # Handle 404 with default error handler for cli.
    cli_handled_err_resp_codes = []

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a formatted response
            Handles 200 responses
        """
        resp_j = response.json()
        return cli_format_common.gen_action_table(resp_j)


class GetConfigdocs(CliAction):
    """Action to Get Configdocs"""

    def __init__(self, ctx, collection, version):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            "GetConfigdocs action initialized with collection=%s and "
            "version=%s" % (collection, version))
        self.collection = collection
        self.version = version

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_configdocs.")
        return self.get_api_client().get_configdocs(
            collection_id=self.collection, version=self.version)

    # Handle 404 with default error handler for cli.
    cli_handled_err_resp_codes = [404]

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        Effectively passes through the YAML received.
        :param response: a requests response object
        :returns: a string representing a CLI appropriate response
            Handles 200 responses
        """
        return format_utils.raw_format_response_handler(response)


class GetConfigdocsStatus(CliAction):
    """Action to get the configdocs status"""

    def __init__(self, ctx):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug("GetConfigdocsStatus action initialized")

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_configdocs_status")
        return self.get_api_client().get_configdocs_status()

    # Handle 404 with default error handler for cli.
    cli_handled_err_resp_codes = [404]

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a CLI appropriate response
            Handles 200 responses
        """
        resp_j = response.json()
        coll_list = resp_j if resp_j else []
        return cli_format_common.gen_collection_table(coll_list)


class GetRenderedConfigdocs(CliAction):
    """Action to Get Rendered Configdocs"""

    def __init__(self, ctx, version):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug("GetRenderedConfigdocs action initialized")
        self.version = version

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_rendereddocs.")
        return self.get_api_client().get_rendereddocs(version=self.version)

    # Handle 404 with default error handler for cli.
    cli_handled_err_resp_codes = [404]

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        Effectively passes through the YAML received.
        :param response: a requests response object
        :returns: a string representing a CLI appropriate response
            Handles 200 responses
        """
        return format_utils.raw_format_response_handler(response)


class GetWorkflows(CliAction):
    """Action to get workflows"""

    def __init__(self, ctx, since=None):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug("GetWorkflows action initialized.")
        self.since = since

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_actions.")
        return self.get_api_client().get_workflows(self.since)

    # Handle 404 with default error handler for cli.
    cli_handled_err_resp_codes = [404]

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a formatted response
            Handles 200 responses
        """
        resp_j = response.json()
        wf_list = resp_j if resp_j else []
        return cli_format_common.gen_workflow_table(wf_list)
