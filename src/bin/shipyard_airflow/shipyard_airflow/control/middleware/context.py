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
""" ContextMiddleware handles setting the external marker provided
by the invoker of a service and adds it to the request contest.
"""
from oslo_utils import uuidutils


class ContextMiddleware(object):
    """
    Handle looking at the X-Context_Marker to see if it has value and that
    value is a UUID (or close enough). If not, generate one.
    """

    def process_request(self, req, resp):
        ctx = req.context
        ext_marker = req.get_header('X-Context-Marker')
        if ext_marker is not None and uuidutils.is_uuid_like(ext_marker):
            # external passed in an ok context marker
            ctx.set_external_marker(ext_marker)
        else:
            # use the request id
            ctx.set_external_marker(ctx.request_id)
