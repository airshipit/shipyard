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
"""Tests for drydock_destroy_nodes operator functions"""
import os
from unittest import mock

from airflow.exceptions import AirflowException
import pytest

from shipyard_airflow.plugins.drydock_destroy_nodes import \
    DrydockDestroyNodeOperator
from shipyard_airflow.plugins.drydock_errors import (
    DrydockTaskFailedException,
    DrydockTaskTimeoutException
)


CONF_FILE = os.path.join(os.path.dirname(__file__), 'test.conf')
ALL_SUCCESES = ['node1', 'node2', 'node3']

# The top level result should have all successes specified
TASK_DICT = {
    '0': {
        'result': {
            'successes': ['node1', 'node2', 'node3'],
            'status': 'success',
        },
        'subtask_id_list': ['1'],
        'status': 'complete'
    },
    '1': {
        'result': {
            'successes': ['node3'],
            'status': 'success',
        },
        'subtask_id_list': ['2', '3'],
        'status': 'complete'
    },
}


def _fake_get_task_dict(task_id):
    return TASK_DICT[task_id]


class TestDrydockDestroyNodesOperator:
    def test_setup_configured_values(self):
        op = DrydockDestroyNodeOperator(main_dag_name="main",
                                        shipyard_conf=CONF_FILE,
                                        task_id="t1")
        op.dc = {
            'physical_provisioner.destroy_interval': 1,
            'physical_provisioner.destroy_timeout': 10,
        }
        op.setup_configured_values()
        assert op.dest_interval == 1
        assert op.dest_timeout == 10

    def test_success_functions(self, caplog):
        op = DrydockDestroyNodeOperator(main_dag_name="main",
                                        shipyard_conf=CONF_FILE,
                                        task_id="t1")
        # testing with lists and sets.
        op.target_nodes = ['n0', 'n1', 'n2']
        op.successes = ['n1']
        caplog.clear()
        op.report_summary()
        assert "  Nodes requested: n0, n1, n2" in caplog.text
        assert "  Nodes destroyed: n1" in caplog.text
        assert "  Nodes not destroyed: n0, n2" in caplog.text
        assert "===== End Destroy" in caplog.text
        assert not op.is_destroy_successful()

        op.target_nodes = set(['n0', 'n1', 'n2'])
        op.successes = []
        caplog.clear()
        op.report_summary()
        assert "  Nodes requested: n0, n1, n2" in caplog.text
        assert "  Nodes destroyed: " in caplog.text
        assert "  Nodes not destroyed: n0, n1, n2" in caplog.text
        assert "===== End Destroy" in caplog.text
        assert not op.is_destroy_successful()

        op.target_nodes = set(['n0', 'n1', 'n2'])
        op.successes = set(['n0', 'n1', 'n2'])
        caplog.clear()
        op.report_summary()
        assert "  Nodes requested: n0, n1, n2" in caplog.text
        assert "  Nodes destroyed: n0, n1, n2" in caplog.text
        assert "  Nodes not destroyed: " in caplog.text
        assert "===== End Destroy" in caplog.text
        assert op.is_destroy_successful()

    @mock.patch.object(
        DrydockDestroyNodeOperator, 'create_task'
    )
    @mock.patch.object(
        DrydockDestroyNodeOperator, 'query_task'
    )
    def test_execute_destroy_simple_success(self, qt, ct, caplog):
        op = DrydockDestroyNodeOperator(main_dag_name="main",
                                        shipyard_conf=CONF_FILE,
                                        task_id="t1")
        op.dc = {
            'physical_provisioner.destroy_interval': 1,
            'physical_provisioner.destroy_timeout': 10,
        }
        op.setup_configured_values()
        op.execute_destroy()
        assert qt.called
        assert ct.called
        assert not caplog.records

    @mock.patch.object(
        DrydockDestroyNodeOperator, 'create_task'
    )
    @mock.patch.object(
        DrydockDestroyNodeOperator, 'query_task',
        side_effect=DrydockTaskFailedException("test")
    )
    def test_execute_destroy_query_fail(self, qt, ct, caplog):
        op = DrydockDestroyNodeOperator(main_dag_name="main",
                                        shipyard_conf=CONF_FILE,
                                        task_id="t1")
        op.dc = {
            'physical_provisioner.destroy_interval': 1,
            'physical_provisioner.destroy_timeout': 10,
        }
        op.setup_configured_values()
        op.execute_destroy()
        assert qt.called
        assert ct.called
        assert "Task destroy_nodes has failed." in caplog.text

    @mock.patch.object(
        DrydockDestroyNodeOperator, 'create_task'
    )
    @mock.patch.object(
        DrydockDestroyNodeOperator, 'query_task',
        side_effect=DrydockTaskTimeoutException("test")
    )
    def test_execute_destroy_query_timeout(self, qt, ct, caplog):
        op = DrydockDestroyNodeOperator(main_dag_name="main",
                                        shipyard_conf=CONF_FILE,
                                        task_id="t1")
        op.dc = {
            'physical_provisioner.destroy_interval': 1,
            'physical_provisioner.destroy_timeout': 10,
        }
        op.setup_configured_values()
        op.execute_destroy()
        assert qt.called
        assert ct.called
        assert "Task destroy_nodes has timed out after 10 seconds." in (
            caplog.text)

    @mock.patch.object(
        DrydockDestroyNodeOperator, 'get_successes_for_task',
        return_value=['n0', 'n1']
    )
    @mock.patch.object(
        DrydockDestroyNodeOperator, 'create_task'
    )
    @mock.patch.object(
        DrydockDestroyNodeOperator, 'query_task',
        side_effect=DrydockTaskTimeoutException("test")
    )
    def test_do_execute_fail(self, qt, ct, gs, caplog):
        op = DrydockDestroyNodeOperator(main_dag_name="main",
                                        shipyard_conf=CONF_FILE,
                                        task_id="t1")
        op.dc = {
            'physical_provisioner.destroy_interval': 1,
            'physical_provisioner.destroy_timeout': 10,
        }
        op.target_nodes = ['n0', 'n1', 'n2']
        with pytest.raises(AirflowException) as ae:
            op.do_execute()
            assert qt.called
            assert ct.called
            assert gs.called
            assert "Task destroy_nodes has timed out after 10 seconds." in (
                caplog.text)
        assert ("One or more nodes requested for destruction failed to "
                "destroy") in str(ae.value)

    @mock.patch.object(
        DrydockDestroyNodeOperator, 'get_successes_for_task',
        return_value=['n0', 'n1', 'n2']
    )
    @mock.patch.object(
        DrydockDestroyNodeOperator, 'create_task'
    )
    @mock.patch.object(
        DrydockDestroyNodeOperator, 'query_task',
    )
    def test_do_execute(self, qt, ct, gs, caplog):
        op = DrydockDestroyNodeOperator(main_dag_name="main",
                                        shipyard_conf=CONF_FILE,
                                        task_id="t1")
        op.dc = {
            'physical_provisioner.destroy_interval': 1,
            'physical_provisioner.destroy_timeout': 10,
        }
        op.target_nodes = ['n0', 'n1', 'n2']
        op.do_execute()
        assert qt.called
        assert ct.called
        assert gs.called
        assert "  Nodes requested: n0, n1, n2" in caplog.text
        assert "  Nodes destroyed: n0, n1, n2" in caplog.text
        assert "  Nodes not destroyed: " in caplog.text
        assert "===== End Destroy" in caplog.text
