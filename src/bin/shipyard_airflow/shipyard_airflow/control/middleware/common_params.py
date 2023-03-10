# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
""" Common Parameter processing middleware

Extracts some common parameters from all requests and sets the value (or a
default) on the request context.
The values processed here are those items that have applicability across
multiple endpoints in the API.
This middleware should not be used for endpoint specific values.
"""
import logging

import falcon

from shipyard_airflow.common.notes.notes import MAX_VERBOSITY
from shipyard_airflow.errors import ApiError

LOG = logging.getLogger(__name__)


class CommonParametersMiddleware(object):
    """Common query parameter processing

    Sets common query parameter values to the request.context in like-named
    fields. E.g.:

      ?verbosity=1 results in req.context.verbosity set to the value 1.
    """
    def process_request(self, req, resp):
        self.verbosity(req)

    def verbosity(self, req):
        """Process the verbosity parameter

        :param req: the Falcon request object
        Valid values range from 0 (none) to 5 (maximum verbosity)
        """

        try:
            verbosity = req.get_param_as_int(
                'verbosity',
                required=False,
                min_value=0,
                max_value=MAX_VERBOSITY
            )
            if verbosity is not None:
                # if not set, retains the context default value.
                req.context.verbosity = verbosity
        except falcon.HTTPBadRequest as hbr:
            LOG.exception(hbr)
            raise ApiError(
                title="Invalid verbosity parameter",
                description=("If specified, verbosity parameter should be a "
                             "value from 0 to {}".format(MAX_VERBOSITY)),
                status=falcon.HTTP_400
            )
