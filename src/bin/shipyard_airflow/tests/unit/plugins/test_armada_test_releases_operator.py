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
"""Tests ArmadaTestReleasesOperator functionality"""
import os
from unittest import mock

from airflow.exceptions import AirflowException
import pytest

from shipyard_airflow.plugins.armada_base_operator import \
    ArmadaBaseOperator
from shipyard_airflow.plugins.armada_test_releases import \
    ArmadaTestReleasesOperator
from shipyard_airflow.plugins.ucp_base_operator import \
    UcpBaseOperator



CONF_FILE = os.path.join(os.path.dirname(__file__), 'test.conf')

ACTION_PARAMS = {
    'release': 'glance'
}

RELEASES = {
    'ucp': ['armada', 'deckhand', 'shipyard'],
    'openstack': ['glance', 'heat', 'horizon', 'keystone']
}


class TestArmadaTestReleasesOperator:
    @mock.patch('shipyard_airflow.plugins.armada_test_releases.LOG.info')
    @mock.patch.object(ArmadaBaseOperator, 'armada_client', create=True)
    @mock.patch.object(ArmadaBaseOperator, 'get_releases',
        return_value=RELEASES)
    def test_do_execute(self, mock_releases, mock_client,
                        mock_logs):
        op = ArmadaTestReleasesOperator(main_dag_name='main',
                                        shipyard_conf=CONF_FILE,
                                        task_id='t1')
        op.action_params = dict()
        op.do_execute()

        # Verify Armada client called to test every release
        calls = list()
        for release_list in RELEASES.values():
            for release in release_list:
                calls.append(mock.call(
                    release=release,
                    timeout=None))
        mock_client.get_test_release.assert_has_calls(calls, any_order=True)

        # Verify test results logged
        mock_logs.assert_called_with(mock_client.get_test_release.return_value)

    @mock.patch('shipyard_airflow.plugins.armada_test_releases.LOG.info')
    @mock.patch.object(ArmadaBaseOperator, 'armada_client', create=True)
    def test_do_execute_with_params(self, mock_client, mock_logs):
        op = ArmadaTestReleasesOperator(main_dag_name='main',
                                        shipyard_conf=CONF_FILE,
                                        task_id='t1')
        op.action_params = ACTION_PARAMS
        op.do_execute()

        # Verify Armada client called for single release with action params
        release = ACTION_PARAMS['release']
        mock_client.get_test_release.assert_called_once_with(
            release=release,
            timeout=None)

        # Verify test results logged
        mock_logs.assert_called_with(mock_client.get_test_release.return_value)

    @mock.patch.object(ArmadaBaseOperator, 'armada_client', create=True)
    @mock.patch.object(ArmadaBaseOperator, 'get_releases',
        return_value=RELEASES)
    @mock.patch.object(UcpBaseOperator, 'get_k8s_logs')
    def test_do_execute_fail(self, mock_k8s_logs,
                             mock_releases, mock_client):
        mock_client.get_test_release.return_value = None

        op = ArmadaTestReleasesOperator(main_dag_name='main',
                                        shipyard_conf=CONF_FILE,
                                        task_id='t1')
        op.action_params = dict()

        # Verify errors logged to pods
        with pytest.raises(AirflowException):
            op.do_execute()
            mock_k8s_logs.assert_called_once()
