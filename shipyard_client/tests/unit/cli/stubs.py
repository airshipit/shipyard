# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import responses

from shipyard_client.cli.action import CliAction
from shipyard_client.cli import format_utils

DEFAULT_AUTH_VARS = {
    'project_domain_name': 'projDomainTest',
    'user_domain_name': 'userDomainTest',
    'project_name': 'projectTest',
    'username': 'usernameTest',
    'password': 'passwordTest',
    'auth_url': 'urlTest'
}

DEFAULT_API_PARAMS = {
    'auth_vars': DEFAULT_AUTH_VARS,
    'context_marker': '88888888-4444-4444-4444-121212121212',
    'debug': False
}

DEFAULT_BODY = """
{
    "message": "Sample status response",
    "details": {
        "messageList": [
            {
                "message": "Message1",
                "error": false
            },
            {
                "message": "Message2",
                "error": false
            }
        ]
    },
    "reason": "Testing"
}
"""

STATUS_TEMPL = """
{{
    "kind": "Status",
    "apiVersion": "v1",
    "metadata": {{}},
    "status": "Valid",
    "message": "{}",
    "reason": "{}",
    "details": {{
        "errorCount": {},
        "messageList": {}
    }},
    "code": {}
}}
"""

STATUS_MSG_TEMPL = """
{{
    "message": "{}-{}",
    "error": {}
}}
"""


def gen_err_resp(message='Err Message',
                 sub_message='Submessage',
                 sub_error_count=1,
                 sub_info_count=0,
                 reason='Reason Text',
                 code=400):
    """Generates a fake status/error response for testing purposes"""
    sub_messages = []
    for i in range(0, sub_error_count):
        sub_messages.append(STATUS_MSG_TEMPL.format(sub_message, i, 'true'))
    for i in range(0, sub_info_count):
        sub_messages.append(STATUS_MSG_TEMPL.format(sub_message, i, 'false'))
    msg_list = '[{}]'.format(','.join(sub_messages))
    resp_str = STATUS_TEMPL.format(message,
                                   reason,
                                   sub_error_count,
                                   msg_list,
                                   code)
    return resp_str


def gen_api_param(auth_vars=None,
                  context_marker='88888888-4444-4444-4444-121212121212',
                  debug=False):
    """Generates an object that is useful as input to a StubCliContext"""
    if auth_vars is None:
        auth_vars = DEFAULT_AUTH_VARS
    return {
        'auth_vars': auth_vars,
        'context_marker': context_marker,
        'debug': debug
    }


class StubCliContext():
    """A stub CLI context that can be configured for tests"""
    def __init__(self,
                 fmt='cli',
                 api_parameters=None):
        if api_parameters is None:
            api_parameters = gen_api_param()
        self.obj = {}
        self.obj['API_PARAMETERS'] = api_parameters
        self.obj['FORMAT'] = fmt


class StubAction(CliAction):
    """A modifiable action that can be used to drive specific behaviors"""
    def __init__(self,
                 ctx,
                 body=DEFAULT_BODY,
                 status_code=200,
                 method='GET'):
        super().__init__(ctx)
        self.body = body
        self.status_code = status_code
        self.method = method

    def invoke(self):
        """Uses responses package to return a fake response"""
        return responses.Response(
            method=self.method,
            url='http://shiptest/stub',
            body=self.body,
            status=self.status_code
        )

    # Handle 404 with default error handler for cli.
    cli_handled_err_resp_codes = [400]

    # Handle 200 responses using the cli_format_response_handler
    cli_handled_succ_resp_codes = [200]

    def cli_format_response_handler(self, response):
        """CLI output handler

        :param response: a requests response object
        :returns: a string representing a formatted response
            Handles 200 responses
        """
        resp_j = response.json()
        return format_utils.table_factory(
            field_names=['Col1', 'Col2'],
            rows=[
                ['message', resp_j.get('message')],
                ['reason', resp_j.get('reason')]
            ]
        )
