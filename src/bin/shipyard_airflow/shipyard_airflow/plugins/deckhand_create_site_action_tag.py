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
from datetime import datetime
import logging
# Using nosec to prevent Bandit blacklist reporting. Subprocess is used
# in a controlled way as part of this operator.
import subprocess  # nosec

from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

from deckhand_base_operator import DeckhandBaseOperator

LOG = logging.getLogger(__name__)


class DeckhandCreateSiteActionTagOperator(DeckhandBaseOperator):

    """Deckhand Create Site Action Tag Operator

    This operator will trigger Deckhand to create a tag for the revision at
    the end of the workflow. The tag will either be 'site-action-success'
    or 'site-action-failure' (dependent upon the result of the workflow).

    """

    def do_execute(self):

        # Calculate total elapsed time for workflow
        time_delta = datetime.now() - self.task_instance.execution_date

        hours, remainder = divmod(time_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        LOG.info('The workflow took %d hr %d mins %d seconds to'
                 ' execute', hours, minutes, seconds)

        LOG.info("Retrieving final state of %s...", self.main_dag_name)

        workflow_result = self.check_workflow_result()

        LOG.info("Creating Site Action Tag for Revision %d", self.revision_id)

        # Create site action tag
        try:
            if workflow_result:
                self.deckhandclient.tags.create(revision_id=self.revision_id,
                                                tag='site-action-success')
            else:
                self.deckhandclient.tags.create(revision_id=self.revision_id,
                                                tag='site-action-failure')

            LOG.info("Site Action Tag created for Revision %d",
                     self.revision_id)

        except:
            # Dump logs from Deckhand pods
            self.get_k8s_logs()

            raise AirflowException("Failed to create revision tag!")

    def check_task_result(self, task_id):

        # Convert Execution Date from datetime format to string
        fmt = '%Y-%m-%dT%H:%M:%S'
        execution_date = self.task_instance.execution_date.strftime(fmt)

        # Retrieve result of task execution
        #
        # TODO(eanylin): Use Airflow API instead of CLI once the API is
        # ready for consumption, i.e. no longer experimental
        response = subprocess.run(
            ['airflow',
             'task_state',
             self.main_dag_name,
             task_id,
             execution_date],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if response.returncode != 0:
            LOG.error("Encountered error while executing Airflow CLI!")

            raise AirflowException(response.stderr.decode('utf-8'))

        else:
            # The result of the task state will be the last element of
            # the list. The task should# either be in 'success' or
            # 'failed' state as all relevant tasks would have completed
            # execution at this point in time.
            result = response.stdout.decode('utf-8').splitlines()[-1]

            LOG.info("Task %s is in %s state", task_id, result)

            return result

    def check_workflow_result(self):

        # Initialize Variables
        task = ['armada_build']
        task_result = {}

        if self.main_dag_name == 'update_site':
            # NOTE: We will check the final state of the 'armada_build' task
            # as a 'success' means that all tasks preceding it would either
            # be in 'skipped' or 'success' state. A failure of 'armada_build'
            # would mean that the workflow has failed. Hence it is sufficient
            # to determine the success/failure of the 'deploy_site' workflow
            # with the final state of the 'armada_build' task.
            #
            # NOTE: The 'update_site' workflow contains additional steps for
            # upgrading of worker pods.
            for k in ['skip_upgrade_airflow', 'upgrade_airflow']:
                task.append(k)

        # Retrieve task result
        for i in task:
            task_result[i] = self.check_task_result(i)

        # Check for failed task(s)
        failed_task = [x for x in task if task_result[x] == 'failed']

        if failed_task:
            LOG.info("Task(s) in the workflow has/have failed: %s",
                     ", ".join(failed_task))

            return False

        else:
            LOG.info("All tasks completed successfully")

            return True


class DeckhandCreateSiteActionTagOperatorPlugin(AirflowPlugin):

    """Creates DeckhandCreateSiteActionTagOperator in Airflow."""

    name = 'deckhand_create_site_action_tag_operator'
    operators = [DeckhandCreateSiteActionTagOperator]
