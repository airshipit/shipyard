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
""" A logging filter to prepend UWSGI-handled formatting to all logging
records that use this filter. Request-based values will cause the log
records to have correlation values that can be used to better trace
logs.  If uwsgi is not present, does not attempt to change the logs in
any way

Threads initiated using threading.Thread can be correlated to the request
they came from by setting a kwarg of log_extra, containing a dictionary
of valeus matching the VALID_ADDL_FIELDS below and any fields that are set
as additional_fields by the setup_logging function. This mechanism assumes
that the thread will maintain the correlation values for the life
of the thread.
"""
import logging
import threading

# Import uwsgi to determine if it has been provided to the application.
try:
    import uwsgi
except ImportError:
    uwsgi = None

VALID_ADDL_FIELDS = ['req_id', 'external_ctx', 'user']
_DEFAULT_LOG_FORMAT = (
    '%(asctime)s %(levelname)-8s %(req_id)s %(external_ctx)s %(user)s '
    '%(module)s(%(lineno)d) %(funcName)s - %(message)s'
)

_LOG_FORMAT_IN_USE = None


def setup_logging(level, format_string=None, additional_fields=None):
    """ Establishes the base logging using the appropriate filter
    attached to the console/stream handler.
    :param level: The level value to set as the threshold for
                  logging. Ideally a client would use logging.INFO or
                  the desired logging constant to set this level value
    :param format_string: Optional value allowing for override of the
                          logging format string. If new values beyond
                          the default value are introduced, the
                          additional_fields must contain those fields
                          to ensure they are set upon using the logging
                          filter.
    :param additional_fields: Optionally allows for specifying more
                              fields that will be set on each logging
                              record. If specified, the format_string
                              parameter should be set with matching
                              fields, otherwise they will not be
                              displayed.
    """
    global _LOG_FORMAT_IN_USE
    _LOG_FORMAT_IN_USE = format_string or _DEFAULT_LOG_FORMAT

    console_handler = logging.StreamHandler()
    if uwsgi:
        console_handler.addFilter(UwsgiLogFilter(additional_fields))
    logging.basicConfig(level=level,
                        format=_LOG_FORMAT_IN_USE,
                        handlers=[console_handler])
    logger = logging.getLogger(__name__)
    logger.info('Established logging defaults')


def get_log_format():
    """ Returns the common log format being used by this application
    """
    return _LOG_FORMAT_IN_USE


def set_logvar(key, value):
    """ Attempts to set the logvar in the request scope , or ignores it
    if not running in uwsgi
    """
    if uwsgi and value:
        uwsgi.set_logvar(key, value)


class UwsgiLogFilter(logging.Filter):
    """ A filter that preepends log records with additional request
    based information, or information provided by log_extra in the
    kwargs provided to a thread
    """
    def __init__(self, additional_fields=None):
        super().__init__()
        if additional_fields is None:
            additional_fields = []
        self.log_fields = [*VALID_ADDL_FIELDS, *additional_fields]

    def filter(self, record):
        """ Checks for thread provided values, or attempts to get values
        from uwsgi
        """
        if self._thread_has_log_extra():
            value_setter = self._set_values_from_log_extra
        else:
            value_setter = self._set_value

        for field_nm in self.log_fields:
            value_setter(record, field_nm)
        return True

    def _set_value(self, record, logvar):
        # handles setting the logvars from uwsgi or '' in case of none/empty
        try:
            logvar_value = None
            if uwsgi:
                logvar_value = uwsgi.get_logvar(logvar)
            if logvar_value:
                setattr(record, logvar, logvar_value.decode('UTF-8'))
            else:
                setattr(record, logvar, '')
        except SystemError:
            # This happens if log_extra is not on a thread that is spawned
            # by a process running under uwsgi
            setattr(record, logvar, '')

    def _set_values_from_log_extra(self, record, logvar):
        # sets the values from the log_extra on the thread
        setattr(record, logvar, self._get_value_from_thread(logvar) or '')

    def _thread_has_log_extra(self):
        # Checks to see if log_extra is present on the current thread
        if self._get_log_extra_from_thread():
            return True
        return False

    def _get_value_from_thread(self, logvar):
        # retrieve the logvar from the log_extra from kwargs for the thread
        return self._get_log_extra_from_thread().get(logvar, '')

    def _get_log_extra_from_thread(self):
        # retrieves the log_extra value from kwargs or {} if it doesn't
        # exist
        return threading.current_thread()._kwargs.get('log_extra', {})
