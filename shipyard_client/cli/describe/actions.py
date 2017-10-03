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
from shipyard_client.cli.output_formatting import output_formatting


class DescribeAction(CliAction):
    """Action to Describe Action"""

    def __init__(self, ctx, action_id):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug(
            "DescribeAction action initialized with action_id=%s", action_id)
        self.action_id = action_id
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_action_detail.")
        self.resp_txt = output_formatting(
            self.output_format,
            self.api_client.get_action_detail(action_id=self.action_id))


class DescribeStep(CliAction):
    """Action to Describe Step"""

    def __init__(self, ctx, action_id, step_id):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug(
            "DescribeStep action initialized with action_id=%s and step_id=%s",
            action_id, step_id)
        self.action_id = action_id
        self.step_id = step_id
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_step_detail.")
        self.resp_txt = output_formatting(self.output_format,
                                          self.api_client.get_step_detail(
                                              action_id=self.action_id,
                                              step_id=self.step_id))


class DescribeValidation(CliAction):
    """Action to Describe Validation"""

    def __init__(self, ctx, action_id, validation_id):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug(
            'DescribeValidation action initialized with action_id=%s'
            'and validation_id=%s', action_id, validation_id)
        self.validation_id = validation_id
        self.action_id = action_id
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_validation_detail.")
        self.resp_txt = output_formatting(
            self.output_format,
            self.api_client.get_validation_detail(
                action_id=self.action_id, validation_id=self.validation_id))
