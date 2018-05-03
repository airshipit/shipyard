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
import json
import yaml

from prettytable import PrettyTable
from prettytable.prettytable import PLAIN_COLUMNS

_INDENT = ' ' * 8


def cli_format_error_handler(response):
    """Generic handler for standard Shipyard error responses

    Method is intended for use when there is no special handling needed
    for the response.
    :param client_response: a requests response object assuming the
        standard error format
    :returns: a generically formatted error response formulated from the
        client_repsonse.  The response will be in the format:

    Error: {{message}}
    Reason: {{Reason}}
    Additional: {{details message list messages}}
    ...
    """
    return cli_format_status_handler(response, is_error=True)


def cli_format_status_handler(response, is_error=False):
    """Handler for standard Shipyard status and status-based error responses

    Method is intended for use when there is no special handling needed
    for the response. If the response is empty, returns empty string
    :param client_response: a requests response object assuming the
        standard error format
    :is_error: toggles the use of status or error verbiage
    :returns: a generically formatted error response formulated from the
        client_repsonse.  The response will be in the format:

    [Error|Status]: {{message}}
    Reason: {{Reason}}
    Additional: {{details message list messages}}
    ...
    """
    formatted = "Error: {}\nReason: {}" if is_error \
        else "Status: {}\nReason: {}"
    try:
        if response.text:
            resp_j = response.json()
            resp = formatted.format(resp_j.get('message', 'Not specified'),
                                    resp_j.get('reason', 'Not specified'))
            # lvl_counts must have a matching number of values as the
            # _LEVEL_KEYS below + 1 for sentinel.
            lvl_counts = [0, 0, 0, 0]
            if resp_j.get('details'):
                mlist = resp_j['details'].get('messageList', [])
                # Decorate messages with level number and sortkey
                for message in mlist:
                    message['lnum'], message['sortkey'] = _lvl_key(
                        message.get('level'),
                        message.get('error', False)
                    )
                # Sort and formulate the messages
                for message in sorted(mlist, key=lambda m: m['sortkey']):
                    lnum = message['lnum']
                    lvl_counts[lnum] = lvl_counts[lnum] + 1
                    if message.get('kind') == 'ValidationMessage':
                        resp = resp + _format_validation_message(message)
                    else:
                        resp = resp + _format_basic_message(message)
                    if message.get('source'):
                        resp = resp + "\n{}Source: {}".format(
                            _INDENT,
                            message['source']
                        )
                # Append a count summary
                resp = resp + ("\n\n####  Errors: {},"
                               " Warnings: {},"
                               " Infos: {},"
                               " Other: {}  ####".format(*lvl_counts))
            return resp
        else:
            return ''
    except ValueError:
        return "Error: Unable to decode response. Value: {}".format(
            response.text)


# Map of levels by severity. Extra values are included in this map but valid
# values are defined here:
# https://github.com/att-comdev/ucp-integration/blob/master/docs/source/api-conventions.rst#validationmessage-message-type
_LEVEL_KEYS = {
    0: ['error', 'fatal'],
    1: ['warn', 'warning'],
    2: ['info', 'debug'],
}
_SENTINEL_SORT_KEY = "3none"
_SENTINEL_LEVEL = 3


def _lvl_key(level_name, error):
    """Generate a level key value and sort key

    Returns a value to support sort order based on lvls dict.
    The result is that like-level items are sorted together.
    The level number provides sameness for levels that are named differently
    but are the same level for our purposes. The sort key retains the original
    provided level so that like named items still sort together.
    """
    if level_name is None:
        if (error):
            level_name = 'error'
        else:
            level_name = 'info'
    else:
        level_name = level_name.lower()

    for key, val_list in _LEVEL_KEYS.items():
        if level_name in val_list:
            return key, '{}{}'.format(key, level_name)
    return _SENTINEL_LEVEL, _SENTINEL_SORT_KEY


def _format_validation_message(message):
    """Formats a ValidationMessage

    Returns a single string with embedded newlines
    """
    resp = '\n- {}: {}'.format(message.get('level'), message.get('name'))
    resp = resp + '\n{}Message: {}'.format(_INDENT, message.get('message'))
    if message.get('diagnostic'):
        resp = resp + '\n{}Diagnostic: {}'.format(
            _INDENT, message.get('diagnostic')
        )
    for doc in message.get('documents', []):
        resp = resp + '\n{}Document: {} - {}'.format(
            _INDENT,
            doc.get('schema'),
            doc.get('name')
        )
    return resp


def _format_basic_message(message):
    """Formats a basic message

    Returns a single string with embedded newlines
    """
    if message.get('error', False):
        resp = '\n- Error: {}'.format(message.get('message'))
    else:
        resp = '\n- Info: {}'.format(message.get('message'))
    return resp


def raw_format_response_handler(response):
    """Basic format handler to return raw response text"""
    return response.text


def formatted_response_handler(response):
    """Base format handler for either json or yaml depending on call"""
    call = response.headers['Content-Type']
    if 'json' in call:
        try:
            return json.dumps(response.json(), sort_keys=True, indent=4)
        except ValueError:
            return (
                "This is not json and could not be printed as such. \n" +
                response.text
            )

    else:  # all others should be yaml
        try:
            return (yaml.dump_all(
                yaml.safe_load_all(response.content),
                width=79,
                indent=4,
                default_flow_style=False))
        except ValueError:
            return (
                "This is not yaml and could not be printed as such.\n" +
                response.text
            )


def table_factory(field_names=None, rows=None, style=None):
    """Generate a table using prettytable

    Factory method for a prettytable using the PLAIN_COLUMN style unless
    ovrridden by the style parameter.
    If a field_names list of strings is passed in, the column names
    will be initialized.
    If rows are supplied (list of lists), the will be added as rows in
    order.
    """
    p = PrettyTable()
    if style is None:
        p.set_style(PLAIN_COLUMNS)
    else:
        p.set_style(style)
    if field_names:
        p.field_names = field_names
    else:
        p.header = False
    if rows:
        for row in rows:
            p.add_row(row)

    # This alignment only works if columns and rows are set up.
    # Left alignment is used by default
    p.align = 'l'

    return p


def table_get_string(table, title='', vertical_char='|', align='l'):
    """Wrapper to return a prettytable string with the supplied alignment"""
    table.align = align

    # Title is an empty string by default
    # vertical_char - Single character string used to draw vertical
    # lines. Default is '|'.
    return table.get_string(title=title, vertical_char=vertical_char)
