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
"""
Helper class for workflows/inquiry API classes, encapsulating data access
"""
import logging

import arrow
from arrow.parser import ParserError

from shipyard_airflow.db.db import AIRFLOW_DB

LOG = logging.getLogger(__name__)


class WorkflowHelper(object):
    """
    WorkflowHelper provides a layer to represent encapsulation of data
    access for the Airflow Monitoring API.

    A new WorkflowHelper is intended to be used for each invocation
    of the service, so as to keep the context_marker associated
    with the invoking user.
    """

    def __init__(self, context_marker):
        """ Sets up this helper with the supplied context marker

        :param context_marker: a UUID marker used for correlation
        """
        self.context_marker = context_marker

    @staticmethod
    def _add_id_to_run(dag_run):
        # generates the id values for the dag_run and returns it
        time_string = None
        if dag_run.get('execution_date') is not None:
            dag_exec_tm = arrow.get(dag_run.get('execution_date'))
            time_string = (dag_exec_tm.format('YYYY-MM-DDTHH:mm:ss.SSSSSS'))

        dag_run['workflow_id'] = '{}__{}'.format(
            dag_run.get('dag_id'),
            time_string
        )
        return dag_run

    @staticmethod
    def _split_workflow_id_to_dag_run(workflow_id):
        # translates standard {dag_id}__{execution_date} format to a
        # dictionary:
        # {'dag_id': <dag_id>, 'execution_date':<execution_date> }
        if '__' in workflow_id:
            dag_id, execution_date = workflow_id.rsplit('__', 1)
            return {
                'dag_id': dag_id,
                'execution_date': execution_date
            }
        return {}

    @staticmethod
    def validate_workflow_id(workflow_id):
        """
        checks that the workflow_id contains the separator '__' to pass
        minimal identificaiton as a valid workflow_id:
        {dag_id}__{execution_date}
        """
        return workflow_id is not None and '__' in workflow_id

    @staticmethod
    def _get_threshold_date(since_iso8601=None):
        # generates the threshold date from the input. Defaults to
        # 30 days prior to UTC now.
        threshold_date = None
        if since_iso8601 is None:
            threshold_date = arrow.utcnow().shift(days=-30)
        else:
            try:
                threshold_date = arrow.get(since_iso8601)
            except ParserError as parser_err:
                LOG.error(
                    'Unable to parse date from %s. Error: %s, defaulting to '
                    'now minus 30 days',
                    since_iso8601,
                    str(parser_err)
                )
                threshold_date = arrow.utcnow().shift(days=-30)
        return threshold_date.naive

    def get_workflow_list(self, since_iso8601=None):
        """
        Returns all top level workflows, filtering by the supplied
        since_iso8601 value.
        :param since_iso8601: An iso8601 format specifying a date
        boundary. Optional, defaults to 30 days prior
        :returns: a list of workflow dictionaries
        """
        threshold_date = WorkflowHelper._get_threshold_date(
            since_iso8601=since_iso8601
        )
        dag_runs = self._get_all_dag_runs_db()
        # only dags meeting the date criteria and are not subdags
        # by convention subdags are parent.child named.
        return [
            WorkflowHelper._add_id_to_run(run) for run in dag_runs
            if ('.' not in run.get('dag_id') and
                arrow.get(run.get('execution_date')).naive >= threshold_date)
        ]

    def get_workflow(self, workflow_id):
        """
        Retrieves the workflow(DAG) and associated steps from airflow
        using key derived from workflow_id
        :returns: the workflow dictionary or {} if it cannot be found
        """
        dag_info = WorkflowHelper._split_workflow_id_to_dag_run(workflow_id)

        # input should have been validated previously.
        if not dag_info:
            return {}

        workflow_list = self._get_dag_run_like_id_db(**dag_info)
        if not workflow_list:
            return {}
        # workflow list contains parent and all child dags. Sort them
        workflow_list.sort(key=lambda workflow: workflow.get('dag_id'))

        # add the workflow id to each one
        for workflow_item in workflow_list:
            WorkflowHelper._add_id_to_run(workflow_item)

        # extract the parent workflow, and add the rest as children.
        workflow = workflow_list[0]
        workflow['sub_dags'] = workflow_list[1:]
        workflow['steps'] = self._get_tasks_list(workflow_id)
        return workflow

    def _get_tasks_list(self, workflow_id):
        """
        Returns the task list for a specified dag run derived from the
        workflow_id (dag_id, execution_date)
        """
        # NOTE (bryan-strassner) This currently is just a simple passthrough,
        #                        but is anticipated to do more manipulation of
        #                        the data in the future.
        dag_info = WorkflowHelper._split_workflow_id_to_dag_run(workflow_id)

        # input should have been validated previously.
        if not dag_info:
            return []

        return self._get_tasks_by_id_db(**dag_info)

    def _get_all_dag_runs_db(self):
        """
        Wrapper for call to the airflow database to get all actions
        :returns: a list of dag_runs dictionaries
        """
        return AIRFLOW_DB.get_all_dag_runs()

    def _get_dag_run_like_id_db(self, dag_id, execution_date):
        """
        Wrapper for call to the airflow database to get a single action
        by id
        """
        return AIRFLOW_DB.get_dag_runs_like_id(
            dag_id=dag_id, execution_date=execution_date
        )

    def _get_tasks_by_id_db(self, dag_id, execution_date):
        """
        Wrapper for call to the airflow db to get all tasks
        :returns: a list of task dictionaries
        """
        return AIRFLOW_DB.get_tasks_by_id(
            dag_id=dag_id,
            execution_date=execution_date
        )
