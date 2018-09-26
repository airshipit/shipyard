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
"""Tests for drydock base operator functions"""
import os
from unittest import mock

import pytest

from shipyard_airflow.plugins.drydock_verify_site import (
    DrydockVerifySiteOperator
)
from shipyard_airflow.plugins.drydock_errors import (
    DrydockTaskFailedException,
)

CONF_FILE = os.path.join(os.path.dirname(__file__), 'test.conf')


@mock.patch('shipyard_airflow.plugins.ucp_base_operator.get_pod_logs')
def test_logs_fetched_if_exception_in_create_task(get_pod_logs):
    client = mock.MagicMock()
    err = 'Fake create task method failed'
    client.create_task.side_effect = ValueError(err)
    dvs = DrydockVerifySiteOperator(
        task_id="t1",
        shipyard_conf=CONF_FILE,
        drydock_client=client)
    dvs._deckhand_design_ref = mock.MagicMock()
    dvs._continue_processing_flag = mock.MagicMock(return_value=True)
    dvs._setup_drydock_client = mock.MagicMock()
    with pytest.raises(ValueError, match=err):
        dvs.execute(mock.MagicMock())
    assert get_pod_logs.called
    assert client.get_tasks.called


@mock.patch('time.sleep', mock.MagicMock())
@mock.patch('shipyard_airflow.plugins.ucp_base_operator.get_pod_logs')
def test_logs_fetched_if_exception_in_query_task(get_pod_logs):
    client = mock.MagicMock()
    dvs = DrydockVerifySiteOperator(
        task_id="t1",
        shipyard_conf=CONF_FILE,
        drydock_client=client)
    dvs._deckhand_design_ref = mock.MagicMock()
    dvs._continue_processing_flag = mock.MagicMock(return_value=True)
    dvs._setup_drydock_client = mock.MagicMock()
    with pytest.raises(DrydockTaskFailedException):
        dvs.execute(mock.MagicMock())
    assert get_pod_logs.called
    assert client.get_tasks.called
