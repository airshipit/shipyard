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


class GetActions(CliAction):
    """Action to Get Actions"""

    def __init__(self, ctx):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug("GetActions action initialized.")
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_actions.")
        self.resp_txt = output_formatting(self.output_format,
                                          self.api_client.get_actions())


class GetConfigdocs(CliAction):
    """Action to Get Configdocs"""

    def __init__(self, ctx, collection, version):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug(
            "GetConfigdocs action initialized with collection=%s and "
            "version=%s" % (collection, version))
        self.collection = collection
        self.version = version
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_configdocs.")
        self.resp_txt = output_formatting(self.output_format,
                                          self.api_client.get_configdocs(
                                              collection_id=self.collection,
                                              version=self.version))


class GetRenderedConfigdocs(CliAction):
    """Action to Get Rendered Configdocs"""

    def __init__(self, ctx, version):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.logger.debug("GetRenderedConfigdocs action initialized")
        self.version = version
        self.output_format = ctx.obj['FORMAT']

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client get_rendereddocs.")
        self.resp_txt = output_formatting(
            self.output_format,
            self.api_client.get_rendereddocs(version=self.version))
