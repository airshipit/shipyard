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
import falcon
from oslo_config import cfg

from shipyard_airflow import policy
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.control.af_monitoring.workflow_helper import (
    WorkflowHelper
)
from shipyard_airflow.errors import ApiError

CONF = cfg.CONF


class WorkflowResource(BaseResource):
    """
    API handler for /workflows invocations
    /api/v1.0/workflows
    """

    @policy.ApiEnforcer('workflow_orchestrator:list_workflows')
    def on_get(self, req, resp):
        """
        Return actions that have been invoked through shipyard.
        :returns: a json array of workflow entities
        """
        since_date = req.params.get('since')
        helper = WorkflowHelper(req.context.external_marker)
        resp.body = self.to_json(
            self.get_all_workflows(helper=helper, since_date=since_date)
        )
        resp.status = falcon.HTTP_200

    def get_all_workflows(self, helper, since_date=None):
        """
        Retrieve all workflows from airflow that have occurred,
        using the since_date (iso8601) as a boundary.
        :param helper: The WorkflowHelper constructed for this invocation
        :param since_date: a Date string in iso8601 or None
        :returns: a list of workflow dictionaries
        """
        return helper.get_workflow_list(since_iso8601=since_date)


class WorkflowIdResource(BaseResource):
    """
    API handler for /workflows/{workflow_id} invocations
    /api/v1/workflows/{workflow_id}
    """

    @policy.ApiEnforcer('workflow_orchestrator:get_workflow')
    def on_get(self, req, resp, workflow_id):
        """
        Retrieve the step details of workflows invoked in Airflow.
        :returns: a json object of a workflow entity
        """
        helper = WorkflowHelper(req.context.external_marker)
        resp.body = self.to_json(
            self.get_workflow_detail(helper=helper, workflow_id=workflow_id)
        )
        resp.status = falcon.HTTP_200

    def get_workflow_detail(self, helper, workflow_id):
        """
        Retrieve a workflow by id,
        :param helper: The WorkflowHelper constructed for this invocation
        :param workflow_id: a string in {dag_id}__{execution_date} format
                            identifying a workflow
        :returns: a workflow detail dictionary including steps
        """
        if not WorkflowHelper.validate_workflow_id(workflow_id):
            raise ApiError(
                title='Invalid Workflow ID specified',
                description=(
                    'Workflow id must use {dag id}__{execution date} format',
                ),
                status=falcon.HTTP_400,
                retry=False,
            )
        workflow = helper.get_workflow(workflow_id=workflow_id)
        if workflow is None:
            raise ApiError(
                title='Workflow not found',
                description=(
                    'A Workflow with id {} was not found'.format(workflow_id),
                ),
                status=falcon.HTTP_404,
                retry=False,
            )
        return workflow
