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
import mock

import responses

from shipyard_client.api_client.base_client import BaseClient
from shipyard_client.cli.commit.actions import CommitConfigdocs
from shipyard_client.tests.unit.cli import stubs


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_commit_configdocs(*args):
    responses.add(responses.POST,
                  'http://shiptest/commitconfigdocs?force=false',
                  body=None,
                  status=200)
    response = CommitConfigdocs(stubs.StubCliContext(),
                                False, False).invoke_and_return_resp()
    assert response == 'Configuration documents committed.\n'


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_commit_configdocs_409(*args):
    api_resp = stubs.gen_err_resp(message="Conflicts message",
                                  sub_message='Another bucket message',
                                  sub_error_count=1,
                                  sub_info_count=0,
                                  reason='Conflicts reason',
                                  code=409)
    responses.add(responses.POST,
                  'http://shiptest/commitconfigdocs?force=false',
                  body=api_resp,
                  status=409)
    response = CommitConfigdocs(stubs.StubCliContext(),
                                False, False).invoke_and_return_resp()
    assert 'Error: Conflicts message' in response
    assert 'Configuration documents committed' not in response
    assert 'Reason: Conflicts reason' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_commit_configdocs_forced(*args):
    api_resp = stubs.gen_err_resp(message="Conflicts message forced",
                                  sub_message='Another bucket message',
                                  sub_error_count=1,
                                  sub_info_count=0,
                                  reason='Conflicts reason',
                                  code=200)
    responses.add(responses.POST,
                  'http://shiptest/commitconfigdocs?force=true',
                  body=api_resp,
                  status=200)
    response = CommitConfigdocs(stubs.StubCliContext(),
                                True, False).invoke_and_return_resp()
    assert 'Status: Conflicts message forced' in response
    assert 'Configuration documents committed' in response
    assert 'Reason: Conflicts reason' in response


@responses.activate
@mock.patch.object(BaseClient, 'get_endpoint', lambda x: 'http://shiptest')
@mock.patch.object(BaseClient, 'get_token', lambda x: 'abc')
def test_commit_configdocs_dryrun(*args):
    responses.add(responses.POST,
                  'http://shiptest/commitconfigdocs?force=false',
                  body=None,
                  status=200)
    response = CommitConfigdocs(stubs.StubCliContext(),
                                False, True).invoke_and_return_resp()
    assert response == ('Configuration documents were not committed. Currently'
                        ' in dryrun mode.\n')
