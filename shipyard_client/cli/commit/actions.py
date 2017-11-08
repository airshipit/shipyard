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
from shipyard_client.cli.output_formatting import output_formatting


class CommitConfigdocs(CliAction):
    """Actions to Commit Configdocs"""

    def __init__(self, ctx, force):
        """Initializes api_client, sets parameters, and sets output_format"""
        super().__init__(ctx)
        self.force = force
        self.output_format = ctx.obj['FORMAT']
        self.logger.debug("CommitConfigdocs action initialized with force=%s",
                          force)

    def invoke(self):
        """Calls API Client and formats response from API Client"""
        self.logger.debug("Calling API Client commit_configdocs.")
        self.resp_txt = output_formatting(
            self.output_format,
            self.api_client.commit_configdocs(force=self.force))
