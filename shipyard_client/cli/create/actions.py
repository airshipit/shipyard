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


class CreateAction(CliAction):
    """Action to Create Action"""

    def __init__(self, ctx, action_name, param):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug("CreateAction action initialized with action command"
                          "%s and parameters %s", action_name, param)
        self.action_name = action_name
        self.param = param
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client post_actions.")
        self.resp_txt = output_formatting(self.output_format,
                                          self.api_client.post_actions(
                                              name=self.action_name,
                                              parameters=self.param))


class CreateConfigdocs(CliAction):
    """Action to Create Configdocs"""

    def __init__(self, ctx, collection, buffer, data):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug("CreateConfigdocs action initialized with" +
                          " collection=%s,buffer=%s and data=%s", collection,
                          buffer, str(data))
        self.collection = collection
        self.buffer = buffer
        self.data = data
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client post_configdocs.")
        self.resp_txt = output_formatting(self.output_format,
                                          self.api_client.post_configdocs(
                                              collection_id=self.collection,
                                              buffer_mode=self.buffer,
                                              document_data=self.data))
