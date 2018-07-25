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
from unittest.mock import patch

from click.testing import CliRunner

from shipyard_client.cli.commands import shipyard
from shipyard_client.api_client.shipyardclient_context import \
    ShipyardClientContext


def test_shipyard():
    context_marker = '--context-marker=88888888-4444-4444-4444-121212121212'
    debug = '--debug'
    os_project_domain_name = (
        '--os-project-domain-name=OS_PROJECT_DOMAIN_NAME_test')
    os_user_domain_name = '--os-user-domain-name=OS_USER_DOMAIN_NAME_test'
    os_project_name = '--os-project-name=OS_PROJECT_NAME_test'
    os_username = '--os-username=OS_USERNAME_test'
    os_password = '--os-password=OS_PASSWORD_test'
    os_auth_url = '--os-auth-url=OS_AUTH_URL_test'

    auth_vars = {
        'project_domain_name': 'OS_PROJECT_DOMAIN_NAME_test',
        'user_domain_name': 'OS_USER_DOMAIN_NAME_test',
        'project_name': 'OS_PROJECT_NAME_test',
        'username': 'OS_USERNAME_test',
        'password': 'OS_PASSWORD_test',
        'auth_url': 'OS_AUTH_URL_test'
    }

    runner = CliRunner()
    with patch.object(ShipyardClientContext, '__init__') as mock_method:
        results = runner.invoke(shipyard, [
            context_marker, os_project_domain_name, os_user_domain_name,
            os_project_name, os_username, os_password, os_auth_url, debug,
            'commit', 'configdocs'
        ])
    mock_method.assert_called_once_with(
        auth_vars,
        '88888888-4444-4444-4444-121212121212',
        True
    )
