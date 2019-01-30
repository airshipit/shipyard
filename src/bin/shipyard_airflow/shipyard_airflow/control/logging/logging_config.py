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
"""Container for logging configuration"""
import logging

from shipyard_airflow.control.logging import request_logging
from shipyard_airflow.control.logging.redaction_formatter import (
    RedactionFormatter
)
LOG = logging.getLogger(__name__)


class LoggingConfig():
    """Encapsulates the properties of a Logging Config

    :param level: The level value to set as the threshold for logging. Ideally
        a client would use logging.INFO or the desired logging constant to set
        this level value
    :param named_levels: A dictionary of 'name': logging.level values that
        configures the minimum logging level for the named logger.
    :param format_string: Optional value allowing for override of the logging
        format string. If new values beyond the default value are introduced,
        the additional_fields must contain those fields to ensure they are set
        upon using the logging filter.
    :param additional_fields: Optionally allows for specifying more fields that
        will be set on each logging record. If specified, the format_string
        parameter should be set with matching fields, otherwise they will not
        be displayed.
    """

    _default_log_format = (
        "%(asctime)s %(levelname)-8s %(req_id)s %(external_ctx)s %(user)s "
        "%(user_id)s %(module)s(%(lineno)d) %(funcName)s - %(message)s")

    def __init__(self,
                 level,
                 named_levels=None,
                 format_string=None,
                 additional_fields=None):
        self.level = level
        # Any false values passed for named_levels should instead be treated as
        # an empty dictionary i.e. no special log levels
        self.named_levels = named_levels or {}
        # Any false values for format string should use the default instead
        self.format_string = format_string or LoggingConfig._default_log_format
        self.additional_fields = additional_fields

    def setup_logging(self):
        """ Establishes the base logging using the appropriate filter
        attached to the console/stream handler.
        """
        console_handler = logging.StreamHandler()
        request_logging.assign_request_filter(console_handler,
                                              self.additional_fields)
        logging.basicConfig(level=self.level,
                            format=self.format_string,
                            handlers=[console_handler])
        for handler in logging.root.handlers:
            handler.setFormatter(RedactionFormatter(handler.formatter))
        logger = logging.getLogger(__name__)
        logger.info('Established logging defaults')
        self._setup_log_levels()

    def _setup_log_levels(self):
        """Sets up the logger levels for named loggers

        :param named_levels: dict to set each of the specified
            logging levels.
        """
        for logger_name, level in self.named_levels.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            LOG.info("Set %s to use logging level %s", logger_name, level)
