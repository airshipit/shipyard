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
import configparser
import logging
import math
from datetime import datetime

from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

from get_k8s_logs import get_pod_logs
from get_k8s_logs import K8sLoggingException
from xcom_puller import XcomPuller

LOG = logging.getLogger(__name__)


class UcpBaseOperator(BaseOperator):

    """UCP Base Operator

    All UCP related workflow operators will use the UCP base
    operator as the parent and inherit attributes and methods
    from this class

    """

    @apply_defaults
    def __init__(self,
                 main_dag_name=None,
                 pod_selector_pattern=None,
                 shipyard_conf=None,
                 start_time=None,
                 sub_dag_name=None,
                 xcom_push=True,
                 *args, **kwargs):
        """Initialization of UcpBaseOperator object.

        :param main_dag_name: Parent Dag
        :param pod_selector_pattern: A list containing the information on
                                     the patterns of the Pod name and name
                                     of the associated container for log
                                     queries. This will allow us to query
                                     multiple components, e.g. MAAS and
                                     Drydock at the same time. It also allows
                                     us to query the logs of specific container
                                     in Pods with multiple containers. For
                                     instance the Airflow worker pod contains
                                     both the airflow-worker container and the
                                     log-rotate container.
        :param shipyard_conf: Location of shipyard.conf
        :param start_time: Time when Operator gets executed
        :param sub_dag_name: Child Dag
        :param xcom_push: xcom usage

        """

        super(UcpBaseOperator, self).__init__(*args, **kwargs)
        self.main_dag_name = main_dag_name
        self.pod_selector_pattern = pod_selector_pattern or []
        self.shipyard_conf = shipyard_conf
        self.start_time = datetime.now()
        self.sub_dag_name = sub_dag_name
        self.xcom_push_flag = xcom_push

    def execute(self, context):

        # Execute UCP base function
        self.ucp_base(context)

        # Execute base function
        self.run_base(context)

        # Exeute child function
        self.do_execute()

    def ucp_base(self, context):

        LOG.info("Running UCP Base Operator...")

        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        # Initialize variable
        self.ucp_namespace = config.get('k8s_logs', 'ucp_namespace')

        # Define task_instance
        task_instance = context['task_instance']

        # Set up and retrieve values from xcom
        self.xcom_puller = XcomPuller(self.main_dag_name, task_instance)
        self.action_info = self.xcom_puller.get_action_info()
        self.dc = self.xcom_puller.get_deployment_configuration()

    def get_k8s_logs(self):
        """Retrieve Kubernetes pod/container logs specified by an opererator

        This method is "best effort" and should not prevent the progress of
        the workflow processing
        """
        if self.pod_selector_pattern:
            for selector in self.pod_selector_pattern:
                # Get difference in current time and time when the
                # operator was first executed (in seconds)
                t_diff = (datetime.now() - self.start_time).total_seconds()

                # Note that we will end up with a floating number for
                # 't_diff' and will need to round it up to the nearest
                # integer
                t_diff_int = int(math.ceil(t_diff))

                try:
                    get_pod_logs(selector['pod_pattern'],
                                 self.ucp_namespace,
                                 selector['container'],
                                 t_diff_int)

                except K8sLoggingException as e:
                    LOG.error(e)

        else:
            LOG.debug("There are no pod logs specified to retrieve")


class UcpBaseOperatorPlugin(AirflowPlugin):

    """Creates UcpBaseOperator in Airflow."""

    name = 'ucp_base_operator_plugin'
    operators = [UcpBaseOperator]
