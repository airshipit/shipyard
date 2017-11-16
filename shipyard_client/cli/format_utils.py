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
            if resp_j.get('details'):
                for message in resp_j.get('details').get('messageList', []):
                    if message.get('error', False):
                        resp = resp + '\n- Error: {}'.format(
                            message.get('message'))
                    else:
                        resp = resp + '\n- Info: {}'.format(
                            message.get('message'))
            return resp
        else:
            return ''
    except ValueError:
        return "Error: Unable to decode response. Value: {}".format(
            response.text)


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
    p.align = 'l'
    return p


def table_get_string(table, align='l'):
    """Wrapper to return a prettytable string with the supplied alignment"""
    table.align = 'l'
    return table.get_string()
