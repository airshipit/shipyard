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
    WorkflowHelper
)
from shipyard_airflow.control.af_monitoring.workflows_api import (
    WorkflowIdResource,
    WorkflowResource
)

from shipyard_airflow.errors import ApiError


def test_get_all_workflows():
    """
    test that get_all_workflows invokes the helper properly
    """
    wr = WorkflowResource()
    with patch.object(WorkflowHelper, 'get_workflow_list') as mock_method:
        helper = WorkflowHelper('')
        wr.get_all_workflows(helper, None)
    mock_method.assert_called_once_with(since_iso8601=None)


def test_get_workflow_detail():
    """
    test that get_workflow_detail properly invokes the helper
    """
    wir = WorkflowIdResource()
    with patch.object(WorkflowHelper, 'get_workflow') as mock_method:
        helper = WorkflowHelper('')
        wir.get_workflow_detail(helper,
                                'deploy_site__1972-04-03T10:00:00.20123')
    mock_method.assert_called_once_with(
        workflow_id='deploy_site__1972-04-03T10:00:00.20123'
    )

    with patch.object(WorkflowHelper, 'get_workflow') as mock_method:
        helper = WorkflowHelper('')
        with pytest.raises(ApiError):
            wir.get_workflow_detail(helper, None)
        with pytest.raises(ApiError):
            wir.get_workflow_detail(helper, 'this is a bad id')
        with pytest.raises(ApiError):
            wir.get_workflow_detail(helper, 'dag_idTexecution_date')
        with pytest.raises(ApiError):
            wir.get_workflow_detail(helper, 'dag_id_execution_date')

        wir.get_workflow_detail(helper, 'dag_id__execution_date')
    mock_method.assert_called_once_with(workflow_id='dag_id__execution_date')
