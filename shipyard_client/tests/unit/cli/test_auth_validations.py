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
import pytest

from shipyard_client.cli.action import AuthValuesError
from shipyard_client.tests.unit.cli import stubs


def test_validate_auth_vars_valid():
    action = stubs.StubAction(stubs.StubCliContext())
    try:
        action.validate_auth_vars()
    except AuthValuesError:
        # Valid parameters should not raise an AuthValuesError
        assert False


def test_validate_auth_vars_missing_required():
    auth_vars = {
        'project_domain_name': 'default',
        'user_domain_name': 'default',
        'project_name': 'service',
        'username': 'shipyard',
        'password': 'password',
        'auth_url': None
    }

    param = stubs.gen_api_param(auth_vars=auth_vars)
    action = stubs.StubAction(stubs.StubCliContext(api_parameters=param))
    with pytest.raises(AuthValuesError):
        try:
            action.validate_auth_vars()
        except AuthValuesError as ex:
            assert 'os_auth_url' in ex.diagnostic
            assert 'os_username' not in ex.diagnostic
            assert 'os_password' not in ex.diagnostic
            raise


def test_validate_auth_vars_missing_required_and_others():
    auth_vars = {
        'project_domain_name': 'default',
        'user_domain_name': 'default',
        'project_name': 'service',
        'username': None,
        'password': 'password',
        'auth_url': None
    }
    param = stubs.gen_api_param(auth_vars=auth_vars)
    action = stubs.StubAction(stubs.StubCliContext(api_parameters=param))
    with pytest.raises(AuthValuesError):
        try:
            action.validate_auth_vars()
        except AuthValuesError as ex:
            assert 'os_auth_url' in ex.diagnostic
            assert 'os_username' in ex.diagnostic
            assert 'os_password' not in ex.diagnostic
            raise
