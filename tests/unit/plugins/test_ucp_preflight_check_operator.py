# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
import pytest
from requests.models import Response

from airflow.exceptions import AirflowException
from shipyard_airflow.plugins.ucp_preflight_check_operator import (
    UcpHealthCheckOperator)

ucp_components = [
    'armada',
    'deckhand',
    'kubernetesprovisioner',
    'physicalprovisioner',
    'shipyard']


def test_drydock_health_skip_update_site():
    """
    Ensure that an error is not thrown due to Drydock health failing during
    update_site or deploy site
    """

    expected_log = ('Drydock did not pass health check. Continuing '
                    'as "continue-on-fail" option is enabled.')

    req = Response()
    req.status_code = None

    action_info = {
        "dag_id": "update_site",
        "parameters": {"continue-on-fail": "true"}
    }

    op = UcpHealthCheckOperator(task_id='test')
    op.action_info = action_info

    with mock.patch('logging.info', autospec=True) as mock_logger:
        op.log_health('physicalprovisioner', req)
    mock_logger.assert_called_with(expected_log)

    action_info = {
        "dag_id": "deploy_site",
        "parameters": {"continue-on-fail": "true"}
    }

    with mock.patch('logging.info', autospec=True) as mock_logger:
        op.log_health('physicalprovisioner', req)
    mock_logger.assert_called_with(expected_log)


def test_failure_log_health():
    """ Ensure an error is thrown on failure for all components.
    """
    action_info = {
        "dag_id": "update_site",
        "parameters": {"something-else": "true"}
    }

    req = Response()
    req.status_code = None

    op = UcpHealthCheckOperator(task_id='test')
    op.action_info = action_info

    for i in ucp_components:
        with pytest.raises(AirflowException) as expected_exc:
            op.log_health(i, req)
        assert "Health check failed" in str(expected_exc)


def test_success_log_health():
    """ Ensure 204 gives correct response for all components
    """
    action_info = {
        "dag_id": "deploy_site",
        "parameters": {"something-else": "true"}
    }

    req = Response()
    req.status_code = 204

    op = UcpHealthCheckOperator(task_id='test')
    op.action_info = action_info

    for i in ucp_components:
        with mock.patch('logging.info', autospec=True) as mock_logger:
            op.log_health(i, req)
        mock_logger.assert_called_with('%s is alive and healthy', i)
