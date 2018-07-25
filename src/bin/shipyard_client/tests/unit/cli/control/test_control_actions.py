# Copyright 2017 AT&T Intellectual Property. All other rights reserved.
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
from unittest import mock

import responses

from shipyard_client.api_client.base_client import BaseClient
from shipyard_client.cli.control.actions import Control
from tests.unit.cli import stubs


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_Control(*args):
    responses.add(
        responses.POST,
        'http://shiptest/actions/01BTG32JW87G0YKA1K29TKNAFX/control/pause',
        body=None,
        status=202
    )
    control_verb = 'pause'
    id = '01BTG32JW87G0YKA1K29TKNAFX'
    response = Control(stubs.StubCliContext(),
                       control_verb,
                       id).invoke_and_return_resp()
    # test correct function was called
    assert response == ('pause successfully submitted for action'
                        ' 01BTG32JW87G0YKA1K29TKNAFX')


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_control_unpause(*args):
    responses.add(
        responses.POST,
        'http://shiptest/actions/01BTG32JW87G0YKA1K29TKNAFX/control/unpause',
        body=None,
        status=202
    )
    control_verb = 'unpause'
    id = '01BTG32JW87G0YKA1K29TKNAFX'
    response = Control(stubs.StubCliContext(),
                       control_verb,
                       id).invoke_and_return_resp()
    # test correct function was called
    assert response == ('unpause successfully submitted for action'
                        ' 01BTG32JW87G0YKA1K29TKNAFX')


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_control_stop(*args):
    responses.add(
        responses.POST,
        'http://shiptest/actions/01BTG32JW87G0YKA1K29TKNAFX/control/stop',
        body=None,
        status=202
    )
    control_verb = 'stop'
    id = '01BTG32JW87G0YKA1K29TKNAFX'
    response = Control(stubs.StubCliContext(),
                       control_verb,
                       id).invoke_and_return_resp()
    # test correct function was called
    assert response == ('stop successfully submitted for action'
                        ' 01BTG32JW87G0YKA1K29TKNAFX')


resp_body = """
{
    "message": "Unable to pause action",
    "details": {
        "messageList": [
            {
                "message": "Conflicting things",
                "error": true
            },
            {
                "message": "Try soup",
                "error": false
            }
        ]
    },
    "reason": "Conflicts"
}
"""


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_control_409(*args):
    responses.add(
        responses.POST,
        'http://shiptest/actions/01BTG32JW87G0YKA1K29TKNAFX/control/pause',
        body=resp_body,
        status=409
    )
    control_verb = 'pause'
    id = '01BTG32JW87G0YKA1K29TKNAFX'
    response = Control(stubs.StubCliContext(),
                       control_verb,
                       id).invoke_and_return_resp()
    # test correct function was called
    assert 'Unable to pause action' in response
