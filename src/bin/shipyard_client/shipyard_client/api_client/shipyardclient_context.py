# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
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
import logging

LOG = logging.getLogger(__name__)


class ShipyardClientContext:
    """A context object for ShipyardClient instances."""

    def __init__(self, keystone_auth, context_marker, debug=False):
        """Shipyard context object

        :param bool debug: true, or false
        :param str context_marker:
        :param dict keystone_auth: auth_url, password, project_domain_name,
               project_name, username, user_domain_name
        """
        self.debug = debug
        if self.debug:
            LOG.setLevel(logging.DEBUG)

        self.keystone_auth = keystone_auth
        self.context_marker = context_marker
