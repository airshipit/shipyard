# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# For testing purposes only


def temporary_context(self, keystone_auth, context_marker, debug=False):
    self.debug = debug
    self.keystone_Auth = keystone_auth
    self.service_type = 'shipyard'
    self.shipyard_endpoint = 'http://shipyard/api/v1.0'
    self.context_marker = context_marker
