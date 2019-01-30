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

from shipyard_airflow.control.logging import request_logging

LOG = logging.getLogger(__name__)
HEALTH_URL = '/health'


class LoggingMiddleware(object):
    """ Sets values to the request scope, and logs request and
    response information
    """
    hdr_exclude = re.compile('x-.*', re.IGNORECASE)

    def process_request(self, req, resp):
        """ Set up values to be logged across the request
        """
        request_logging.set_logvar('req_id', req.context.request_id)
        request_logging.set_logvar('external_ctx', req.context.external_marker)
        request_logging.set_logvar('user', req.context.user)
        request_logging.set_logvar('user_id', req.context.user_id)
        if not req.url.endswith(HEALTH_URL):
            # Log requests other than the health check.
            LOG.info("Request %s %s", req.method, req.url)
            self._log_headers(req.headers)

    def process_response(self, req, resp, resource, req_succeeded):
        """ Log the response information
        """
        ctx = req.context
        resp.append_header('X-Shipyard-Req', ctx.request_id)
        resp_code = self._get_resp_code(resp)

        if req.url.endswith(HEALTH_URL):
            # Only log health checks upon failure. This prevents repeated
            # trivial logging due to constant health checks.
            if not resp_code == 204:
                LOG.error('Health check has failed with response status %s',
                          resp.status)
        else:
            LOG.info('%s %s - %s', req.method, req.uri, resp.status)
            # TODO(bryan-strassner) since response bodies can contain sensitive
            #     information, only logging error response bodies here. When we
            #     have response scrubbing or way to categorize responses in the
            #     future, this may be an appropriate place to utilize it.
            if resp_code >= 400:
                LOG.debug('Errored Response body: %s', resp.body)

    def _log_headers(self, headers):
        """ Log request headers, while scrubbing sensitive values
        """
        for header, header_value in headers.items():
            if not LoggingMiddleware.hdr_exclude.match(header):
                LOG.debug("Header %s: %s", header, header_value)

    def _get_resp_code(self, resp):
        # Falcon response object doesn't have a raw status code.
        # Splits by the first space
        try:
            return int(resp.status.split(" ", 1)[0])
        except ValueError:
            # if for some reason this Falcon response doesn't have a valid
            # status, return a high value sentinel
            return 9999
