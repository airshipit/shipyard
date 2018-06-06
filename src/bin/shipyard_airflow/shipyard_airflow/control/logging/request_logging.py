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
""" A logging filter to prepend request scoped formatting to all logging
records that use this filter. Request-based values will cause the log
records to have correlation values that can be used to better trace
logs.  If no handler that supports a request scope is present, does not attempt
to change the logs in any way

Threads initiated using threading. Thread can be correlated to the request
they came from by setting a kwarg of log_extra, containing a dictionary
of values matching the VALID_ADDL_FIELDS below and any fields that are set
as additional_fields by the setup_logging function. This mechanism assumes
that the thread will maintain the correlation values for the life
of the thread.
"""
import logging

# Import uwsgi to determine if it has been provided to the application.
# Only import the UwsgiLogFilter if uwsgi is present
try:
    import uwsgi
    from shipyard_airflow.control.logging.uwsgi_filter import UwsgiLogFilter
except ImportError:
    uwsgi = None


# BASE_ADDL_FIELDS are fields that will be included in the request based
# logging - these fields need not be set up independently as opposed to the
# additional_fields parameter used below, which allows for more fields beyond
# this default set.
BASE_ADDL_FIELDS = ['req_id', 'external_ctx', 'user']
LOG = logging.getLogger(__name__)


def set_logvar(key, value):
    """ Attempts to set the logvar in the request scope, or ignores it
    if not running in an environment that supports it.
    """
    if value:
        if uwsgi:
            uwsgi.set_logvar(key, value)
        # If there were a different handler than uwsgi, here is where we'd
        # need to set the logvar value for its use.


def assign_request_filter(handler, additional_fields=None):
    """Adds the request-scoped filter log filter to the passed handler

    :param handler: a logging handler, e.g. a ConsoleHandler
    :param additional_fields: fields that will be included in the logging
        records (if a matching logging format is used)
    """
    handler_cls = handler.__class__.__name__
    if uwsgi:
        if additional_fields is None:
            additional_fields = []
        addl_fields = [*BASE_ADDL_FIELDS, *additional_fields]
        handler.addFilter(UwsgiLogFilter(uwsgi, addl_fields))
        LOG.info("UWSGI present, added UWSGI log filter to handler %s",
                 handler_cls)
    # if there are other handlers that would allow for request scoped logging
    # to be set up, we could include those options here.
    else:
        LOG.info("No request based logging filter in the current environment. "
                 "No log filter added to handler %s", handler_cls)
