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
from mock import patch
import pytest

from shipyard_airflow.control.af_monitoring.workflow_helper import (
    WorkflowHelper)
from shipyard_airflow.control.af_monitoring.workflows_api import (
    WorkflowResource, WorkflowIdResource)
from shipyard_airflow.errors import ApiError
from tests.unit.control import common


class TestWorkflowResource():
    @patch.object(WorkflowResource, 'get_all_workflows', common.str_responder)
    def test_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        result = api_client.simulate_get(
            "/api/v1.0/workflows", headers=common.AUTH_HEADERS)
        assert result.status_code == 200

    def test_get_all_workflows(self):
        """
        test that get_all_workflows invokes the helper properly
        """
        wr = WorkflowResource()
        with patch.object(WorkflowHelper, 'get_workflow_list') as mock_method:
            helper = WorkflowHelper('')
            wr.get_all_workflows(helper, None)
        mock_method.assert_called_once_with(since_iso8601=None)


class TestWorkflowIdResource():
    @patch.object(WorkflowIdResource, 'get_workflow_detail',
                  common.str_responder)
    def test_on_get(self, api_client):
        """Validate the on_get method returns 200 on success"""
        result = api_client.simulate_get(
            "/api/v1.0/workflows/123456789", headers=common.AUTH_HEADERS)
        assert result.status_code == 200

    def test_get_workflow_detail_success(self):
        """
        test that get_workflow_detail properly invokes the helper
        """
        wir = WorkflowIdResource()
        with patch.object(WorkflowHelper, 'get_workflow') as mock_method:
            helper = WorkflowHelper('')
            wir.get_workflow_detail(helper,
                                    'deploy_site__1972-04-03T10:00:00.20123')
        mock_method.assert_called_once_with(
            workflow_id='deploy_site__1972-04-03T10:00:00.20123')

    def test_get_workflow_detail_invalid_format(self):
        """
        Assert ApiError 'Invalid Workflow ID specified' is raised when
        workflow ID is not a valid format, otherwise the error is not raised.
        """
        wir = WorkflowIdResource()
        with patch.object(WorkflowHelper, 'get_workflow') as mock_method:
            helper = WorkflowHelper('')
            with pytest.raises(ApiError) as expected_exc:
                wir.get_workflow_detail(helper, None)
            assert "Invalid Workflow ID specified" in str(expected_exc)
            with pytest.raises(ApiError) as expected_exc:
                wir.get_workflow_detail(helper, 'this is a bad id')
            assert "Invalid Workflow ID specified" in str(expected_exc)
            with pytest.raises(ApiError) as expected_exc:
                wir.get_workflow_detail(helper, 'dag_idTexecution_date')
            assert "Invalid Workflow ID specified" in str(expected_exc)
            with pytest.raises(ApiError) as expected_exc:
                wir.get_workflow_detail(helper, 'dag_id_execution_date')
            assert "Invalid Workflow ID specified" in str(expected_exc)
            wir.get_workflow_detail(helper, 'dag_id__execution_date')
        mock_method.assert_called_once_with(
            workflow_id='dag_id__execution_date')

    def test_get_workflow_detail_not_found(self):
        """
        Assert ApiError 'Workflow not found' is raised when get_workflow
        returns None.
        """
        wir = WorkflowIdResource()
        with patch.object(WorkflowHelper, 'get_workflow') as mock_method:
            helper = WorkflowHelper('')
            mock_method.return_value = None
            with pytest.raises(ApiError) as expected_exc:
                wir.get_workflow_detail(helper, 'dag_id__execution_date')
            assert "Workflow not found" in str(expected_exc)
