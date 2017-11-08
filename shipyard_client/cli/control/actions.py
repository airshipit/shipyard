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


class Control(CliAction):
    """Action to Pause Process"""

    def __init__(self, ctx, control_verb, action_id):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.action_id = action_id
        self.control_verb = control_verb
        self.output_format = ctx.obj['FORMAT']
        self.logger.debug("ControlPause action initialized")

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client post_control_action.")
        self.resp_txt = output_formatting(self.output_format,
                                          self.api_client.post_control_action(
                                              action_id=self.action_id,
                                              control_verb=self.control_verb))
