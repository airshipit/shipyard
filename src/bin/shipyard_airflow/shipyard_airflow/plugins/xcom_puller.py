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
import logging

LOG = logging.getLogger(__name__)


class XcomPuller(object):
    """XcomPuller provides a common source to get reused xcom values

    One XcomPuller should be created per task.
    Note: xcom values are found by using the current task instance
        and finding the <dag_name>.<task_name> that the xcom was added
        to the workflow.
        The point of this class is to keep all this very configurable
        naming in one place as much as possible so that changes to
        the dag names and step names have less places to update.
    """

    def __init__(self, main_dag_name, task_instance):
        self.mdn = main_dag_name
        self.ti = task_instance

    def _get_xcom(self, source_task, dag_id=None, key=None, log_result=True):
        """Find and return an xcom value

        :param source_task: The name of the task that wrote the xcom
        :param dag_id: The name of the subdag (of the main DAG) that contained
            the source task. Let this default to None if the task is a direct
            child of the main dag
        :param key: The name of the xcom item that was written by the task. If
            the source task allowed for the step to simply push xcom at the
            end of the step, leave this None.
        :param log_result: boolean to indicate if the value of the xcom should
            be logged upon retreival. This can be nice for investigative
            purposes, but would likely not be good for large or complex
            values.
        """
        if dag_id is None:
            source_dag = self.mdn
        else:
            source_dag = "{}.{}".format(self.mdn, dag_id)
        LOG.info("Retrieving xcom from %s.%s with key %s",
                 source_dag,
                 source_task,
                 key)
        xcom_val = self.ti.xcom_pull(task_ids=source_task,
                                     dag_id=source_dag,
                                     key=key)
        if log_result:
            # log the xcom value - don't put large values in xcom!
            LOG.info(xcom_val)

        return xcom_val

    def get_deployment_configuration(self):
        """Retrieve the deployment configuration dictionary"""
        source_task = 'deployment_configuration'
        source_dag = None
        key = None
        return self._get_xcom(source_task=source_task,
                              dag_id=source_dag,
                              key=key)

    def get_action_info(self):
        """Retrieve the action and action parameter info dictionary

        Extract information related to current workflow. This is a dictionary
        that contains information about the workflow such as action_id, name
        and other related parameters
        """
        source_task = 'action_xcom'
        source_dag = None
        key = 'action'
        return self._get_xcom(source_task=source_task,
                              dag_id=source_dag,
                              key=key)

    def get_action_type(self):
        """Retrieve the action type"""
        source_task = 'action_xcom'
        source_dag = None
        key = 'action_type'
        return self._get_xcom(source_task=source_task,
                              dag_id=source_dag,
                              key=key)

    def get_check_drydock_continue_on_fail(self):
        """Check if 'drydock_continue_on_fail' key exists"""
        source_task = 'ucp_preflight_check'
        source_dag = None
        key = 'drydock_continue_on_fail'
        return self._get_xcom(source_task=source_task,
                              dag_id=source_dag,
                              key=key)
