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
"""Tests for get_k8s_logs functions"""
from unittest import mock

from shipyard_airflow.plugins.get_k8s_logs import get_pod_logs


class Metadata:
    def __init__(self, _name):
        self.name = _name


class Pods:
    def __init__(self, _name):
        self.metadata = Metadata(_name)


class TestGetK8slogs:
    @mock.patch("shipyard_airflow.plugins"
                ".get_k8s_logs.client.CoreV1Api", autospec=True)
    @mock.patch("shipyard_airflow.plugins"
                ".get_k8s_logs.config.load_incluster_config")
    def test_get_pod_logs(self, mock_config, mock_client):
        """Assert that get_pod_logs picks up accurate pods
        get_pod_logs('armada-api', 'ucp', 'armada-api', 3600)

        First case - old logic to find pods with "in"
        Second case - new logic with "starts"
        """
        test_pods = [
            Pods('armada-api-66d5f59856-h9c27'),
            Pods('armada-api-66d5f59856-42zvp'),
            # this is the offender if we use "in" instead of "startwith"
            Pods('clcp-ucp-armada-armada-api-test'),
            Pods('armada-ks-endpoints-6ztcg')
        ]

        mock_client.return_value \
            .list_namespaced_pod.return_value \
            .items = test_pods

        get_pod_logs('armada-api', 'ucp', 'armada-api', 3600)

        mock_client.return_value \
            .read_namespaced_pod_log \
            .assert_any_call(container='armada-api',
                             name='armada-api-66d5f59856-h9c27',
                             namespace='ucp',
                             pretty='true',
                             since_seconds=3600)

        mock_client.return_value \
            .read_namespaced_pod_log \
            .assert_any_call(container='armada-api',
                             name='armada-api-66d5f59856-42zvp',
                             namespace='ucp',
                             pretty='true',
                             since_seconds=3600)
