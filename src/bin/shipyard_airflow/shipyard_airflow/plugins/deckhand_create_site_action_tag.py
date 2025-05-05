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
from datetime import timezone
import logging
import os

import requests
from oslo_config import cfg

from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

try:
    from deckhand_base_operator import DeckhandBaseOperator
except ImportError:
    from shipyard_airflow.plugins.deckhand_base_operator import \
        DeckhandBaseOperator

FAILED_STATUSES = ('failed', 'upstream_failed')
CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class DeckhandCreateSiteActionTagOperator(DeckhandBaseOperator):
    """Deckhand Create Site Action Tag Operator

    This operator will trigger Deckhand to create a tag for the revision at
    the end of the workflow. The tag will either be 'site-action-success'
    or 'site-action-failure' (dependent upon the result of the workflow).

    """

    def do_execute(self, context):

        # Получаем logical_date (время запуска DAG Run)
        dag_run_logical_date = context['dag_run'].logical_date

        # Calculate total elapsed time for workflow
        time_delta = datetime.now(timezone.utc) \
            - dag_run_logical_date

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
            raise AirflowException("Failed to create revision tag!")

    def check_task_result(self, task_id):
        """
        Get the state of a task using Airflow REST API v2
        with JWT authentication.
        """
        dag_id = self.main_dag_name
        run_id = self.task_instance.run_id

        # Get Airflow webserver address from config
        web_server_url = CONF.base.web_server
        api_path = (
            f"api/v2/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}"
        )
        req_url = os.path.join(web_server_url, api_path)
        token_url = os.path.join(web_server_url, "auth/token")
        c_timeout = CONF.base.airflow_api_connect_timeout
        r_timeout = CONF.base.airflow_api_read_timeout

        try:
            # Get JWT token
            token_resp = requests.get(
                token_url, timeout=(c_timeout, r_timeout))
            token_resp.raise_for_status()
            token = token_resp.json().get("access_token")
            if not token:
                raise AirflowException(
                    "Airflow did not return a valid access token.")

            # Prepare headers with token
            headers = {
                "Cache-Control": "no-cache",
                "Authorization": f"Bearer {token}"
            }

            # Make GET request to Airflow API v2
            resp = requests.get(
                req_url, timeout=(c_timeout, r_timeout), headers=headers
            )
            if resp.status_code != 200:
                raise AirflowException(
                    f"Failed to get task state: {resp.text}"
                )
            result = resp.json().get("state")
            LOG.info(
                "Task %s is in %s state for dag_id=%s, run_id=%s",
                task_id, result, dag_id, run_id
            )
            return result

        except requests.RequestException as rex:
            LOG.error("Request to Airflow failed: %s", rex.args)
            raise AirflowException(
                f"Unable to complete request to Airflow: {rex}"
            )

    def check_workflow_result(self):

        # Initialize Variables
        task = ['armada_build.armada_get_releases']
        task_result = {}

        if self.main_dag_name in ['update_site', 'update_software']:
            # NOTE: We will check the final state of the 'armada_build' task
            # as a 'success' means that all tasks preceding it would either
            # be in 'skipped' or 'success' state. A failure of 'armada_build'
            # would mean that the workflow has failed. Hence it is sufficient
            # to determine the success/failure of the 'deploy_site' workflow
            # with the final state of the 'armada_build' task.
            #
            # NOTE: The 'update_site' and 'update_software' workflows contain
            # additional steps for upgrading of worker pods.
            for k in ['skip_upgrade_airflow', 'upgrade_airflow']:
                task.append(k)

        # Retrieve task result
        for i in task:
            task_result[i] = self.check_task_result(i)

        # Check for failed task(s)
        failed_task = [x for x in task if task_result[x] in FAILED_STATUSES]

        if failed_task:
            LOG.info(
                "Either upstream tasks or tasks in the "
                "workflow have failed: %s", ", ".join(failed_task))

            return False

        else:
            LOG.info("All tasks completed successfully")

            return True


class DeckhandCreateSiteActionTagOperatorPlugin(AirflowPlugin):
    """Creates DeckhandCreateSiteActionTagOperator in Airflow."""

    name = 'deckhand_create_site_action_tag_operator'
    operators = [DeckhandCreateSiteActionTagOperator]
