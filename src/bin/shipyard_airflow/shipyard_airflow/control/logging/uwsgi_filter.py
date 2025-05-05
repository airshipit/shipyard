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
"""A UWSGI-dependent implementation of a logging filter allowing for
   request-based logging.
"""
import logging
import threading


class UwsgiLogFilter(logging.Filter):
    """ A filter that preepends log records with additional request
    based information, or information provided by log_extra in the
    kwargs provided to a thread
    """

    def __init__(self, uwsgi, additional_fields=None):
        super().__init__()
        if additional_fields is None:
            additional_fields = []
        self.uwsgi = uwsgi
        self.log_fields = additional_fields

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
            logvar_value = self.uwsgi.get_logvar(logvar)
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
