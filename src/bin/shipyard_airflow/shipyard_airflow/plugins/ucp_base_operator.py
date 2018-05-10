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
import os
from datetime import datetime

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

try:
    import service_endpoint
except ImportError:
    from shipyard_airflow.plugins import service_endpoint

try:
    from get_k8s_logs import get_pod_logs
except ImportError:
    from shipyard_airflow.plugins.get_k8s_logs import get_pod_logs

try:
    from get_k8s_logs import K8sLoggingException
except ImportError:
    from shipyard_airflow.plugins.get_k8s_logs import K8sLoggingException

try:
    from xcom_puller import XcomPuller
except ImportError:
    from shipyard_airflow.plugins.xcom_puller import XcomPuller

from shipyard_airflow.common.document_validators.document_validation_utils \
    import DocumentValidationUtils

try:
    from deckhand_client_factory import DeckhandClientFactory
except ImportError:
    from shipyard_airflow.plugins.deckhand_client_factory import (
        DeckhandClientFactory
    )

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

        :param continue_processing: A boolean value on whether to continue
                                    with the workflow. Defaults to True.
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
        self.continue_processing = True
        self.main_dag_name = main_dag_name
        self.pod_selector_pattern = pod_selector_pattern or []
        self.shipyard_conf = shipyard_conf
        self.start_time = datetime.now()
        self.sub_dag_name = sub_dag_name
        self.xcom_push_flag = xcom_push
        self.doc_utils = _get_document_util(self.shipyard_conf)
        self.endpoints = service_endpoint.ServiceEndpoints(self.shipyard_conf)

    def execute(self, context):

        # Execute UCP base function
        self.ucp_base(context)

        # Execute base function
        self.run_base(context)

        if self.continue_processing:
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
        self.task_instance = context['task_instance']

        # Set up and retrieve values from xcom
        self.xcom_puller = XcomPuller(self.main_dag_name, self.task_instance)
        self.action_info = self.xcom_puller.get_action_info()
        self.dc = self.xcom_puller.get_deployment_configuration()
        self.revision_id = self.action_info['committed_rev_id']
        self.design_ref = self._deckhand_design_ref()

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

    def _deckhand_design_ref(self):
        """Assemble a deckhand design_ref"""
        # Retrieve DeckHand Endpoint Information
        LOG.info("Assembling a design ref using revision: %s",
                 self.revision_id)
        deckhand_svc_endpoint = self.endpoints.endpoint_by_name(
            service_endpoint.DECKHAND
        )
        # This URL will be used to retrieve the Site Design YAMLs
        deckhand_path = "deckhand+{}".format(deckhand_svc_endpoint)
        design_ref = os.path.join(deckhand_path,
                                  "revisions",
                                  str(self.revision_id),
                                  "rendered-documents")
        LOG.info("Design Reference is %s", design_ref)
        return design_ref

    def get_unique_doc(self, schema, name, revision_id=None):
        """Retrieve a specific document from Deckhand

        :param schema: the schema of the document
        :param name: the metadata.name of the document
        :param revision_id: the deckhand revision, or defaults to
            self.revision_id
        Wraps the document_validation_utils call to get the same.
        Returns the sepcified document or raises an Airflow exception.
        """
        if revision_id is None:
            revision_id = self.revision_id

        LOG.info(
            "Retrieve shipyard/DeploymentConfiguration/v1, "
            "deployment-configuration from Deckhand"
        )
        try:
            return self.doc_utils.get_unique_doc(revision_id=revision_id,
                                                 name=name,
                                                 schema=schema)
        except Exception as ex:
            LOG.error("A document was expected to be available: Name: %s, "
                      "Schema: %s, Deckhand revision: %s, but there was an "
                      "error attempting to retrieve it. Since this document's "
                      "contents may be critical to the proper operation of "
                      "the workflow, this is fatal.", schema, name,
                      revision_id)
            LOG.exception(ex)
            # if the document is not found for ANY reason, the workflow is
            # broken. Raise an Airflow Exception.
            raise AirflowException(ex)


def _get_document_util(shipyard_conf):
    """Retrieve an instance of the DocumentValidationUtils"""
    dh_client = DeckhandClientFactory(shipyard_conf).get_client()
    return DocumentValidationUtils(dh_client)


class UcpBaseOperatorPlugin(AirflowPlugin):
    """Creates UcpBaseOperator in Airflow."""
    name = 'ucp_base_operator_plugin'
    operators = [UcpBaseOperator]
