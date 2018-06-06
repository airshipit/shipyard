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
"""A logging formatter that attempts to scrub logged data.

Addresses the OWASP considerations of things that should be excluded:
https://www.owasp.org/index.php/Logging_Cheat_Sheet#Data_to_exclude

These that should not usually be logged:

Avoided by circumstance - no action taken by this formatter:
- Application source code
    - Avoided on a case by case basis
- Session identification values (consider replacing with a hashed value if
  needed to track session specific events)
    - Stateless application logs a transaction correlation ID, but not a
      replayable session id.
- Access tokens
    - Headers with access tokens are excluded in the request/response logging

Formatter provides scrubbing facilities:
- Authentication passwords
- Database connection strings
- Encryption keys and other master secrets
"""
import logging

from shipyard_airflow.control.util.redactor import Redactor


LOG = logging.getLogger(__name__)
# Concepts from https://www.relaxdiego.com/2014/07/logging-in-python.html


class RedactionFormatter(object):
    """ A formatter to remove sensitive information from logs
    """
    def __init__(self, original_formatter):
        self.original_formatter = original_formatter
        self.redactor = Redactor()
        LOG.info("RedactionFormatter wrapping %s",
                 original_formatter.__class__.__name__)

    def format(self, record):
        msg = self.original_formatter.format(record)
        return self.redactor.redact(msg)

    def __getattr__(self, attr):
        return getattr(self.original_formatter, attr)
