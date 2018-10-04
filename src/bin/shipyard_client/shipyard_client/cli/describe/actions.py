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


class DescribeAction(CliAction):
    """Action to Describe Action"""

    def __init__(self, ctx, action_id):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            "DescribeAction action initialized with action_id=%s", action_id)
        self.action_id = action_id

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_action_detail.")
        return self.get_api_client().get_action_detail(
            action_id=self.action_id)

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
        # Assemble the sections of the action details
        return '{}\n\n{}\n\n{}\n\n{}\n\n{}\n'.format(
            cli_format_common.gen_action_details(resp_j),
            cli_format_common.gen_action_steps(resp_j.get('steps'),
                                               resp_j.get('id')),
            cli_format_common.gen_action_commands(resp_j.get('command_audit')),
            cli_format_common.gen_action_validations(
                resp_j.get('validations')
            ),
            cli_format_common.gen_detail_notes(resp_j)
        )


class DescribeStep(CliAction):
    """Action to Describe Step"""

    def __init__(self, ctx, action_id, step_id):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            "DescribeStep action initialized with action_id=%s and step_id=%s",
            action_id, step_id)
        self.action_id = action_id
        self.step_id = step_id

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_step_detail.")
        return self.get_api_client().get_step_detail(action_id=self.action_id,
                                                     step_id=self.step_id)

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
        return "{}\n\n{}\n".format(
            cli_format_common.gen_action_step_details(resp_j, self.action_id),
            cli_format_common.gen_detail_notes(resp_j)
        )


class DescribeValidation(CliAction):
    """Action to Describe Validation"""

    def __init__(self, ctx, action_id, validation_id):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            'DescribeValidation action initialized with action_id=%s'
            'and validation_id=%s', action_id, validation_id)
        self.validation_id = validation_id
        self.action_id = action_id

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_validation_detail.")
        return self.get_api_client().get_validation_detail(
            action_id=self.action_id, validation_id=self.validation_id)

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
        val_list = [resp_j] if resp_j else []
        return cli_format_common.gen_action_validations(val_list)


class DescribeWorkflow(CliAction):
    """Action to describe a workflow"""

    def __init__(self, ctx, workflow_id):
        """Sets parameters."""
        super().__init__(ctx)
        self.logger.debug(
            "DescribeWorkflow action initialized with workflow_id=%s",
            workflow_id)
        self.workflow_id = workflow_id

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_action_detail.")
        return self.get_api_client().get_dag_detail(
            workflow_id=self.workflow_id)

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
        # Assemble the workflow details

        return '{}\n\n{}\n\nSubworkflows:\n{}\n'.format(
            cli_format_common.gen_workflow_details(resp_j),
            cli_format_common.gen_workflow_steps(resp_j.get('steps', [])),
            cli_format_common.gen_sub_workflows(resp_j.get('sub_dags', []))
        )
