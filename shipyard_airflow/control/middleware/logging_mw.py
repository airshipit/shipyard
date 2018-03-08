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
""" Module for logging related middleware
"""
import logging
import re

from shipyard_airflow.control import ucp_logging

LOG = logging.getLogger(__name__)


class LoggingMiddleware(object):
    """ Sets values to the request scope, and logs request and
    response information
    """
    hdr_exclude = re.compile('x-.*', re.IGNORECASE)

    def process_request(self, req, resp):
        """ Set up values to be logged across the request
        """
        ucp_logging.set_logvar('req_id', req.context.request_id)
        ucp_logging.set_logvar('external_ctx', req.context.external_marker)
        ucp_logging.set_logvar('user', req.context.user)
        LOG.info("Request %s %s", req.method, req.url)
        self._log_headers(req.headers)

    def process_response(self, req, resp, resource, req_succeeded):
        """ Log the response information
        """
        ctx = req.context
        resp.append_header('X-Shipyard-Req', ctx.request_id)
        LOG.info('%s %s - %s', req.method, req.uri, resp.status)
        LOG.debug('Response body:%s', resp.body)

    def _log_headers(self, headers):
        """ Log request headers, while scrubbing sensitive values
        """
        for header, header_value in headers.items():
            if not LoggingMiddleware.hdr_exclude.match(header):
                LOG.debug("Header %s: %s", header, header_value)
