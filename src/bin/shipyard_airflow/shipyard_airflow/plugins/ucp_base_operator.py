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
import sqlalchemy

try:
    from deckhand_client_factory import DeckhandClientFactory
    import service_endpoint
    from get_k8s_logs import get_pod_logs
    from get_k8s_logs import K8sLoggingException
    from service_token import shipyard_service_token
    from xcom_puller import XcomPuller
except ImportError:
    from shipyard_airflow.plugins.deckhand_client_factory import \
        DeckhandClientFactory
    from shipyard_airflow.plugins import service_endpoint
    from shipyard_airflow.plugins.get_k8s_logs import get_pod_logs
    from shipyard_airflow.plugins.get_k8s_logs import K8sLoggingException
    from shipyard_airflow.plugins.service_token import shipyard_service_token
    from shipyard_airflow.plugins.xcom_puller import XcomPuller

from shipyard_airflow.common.document_validators.document_validation_utils \
    import DocumentValidationUtils
from shipyard_airflow.common.notes.notes import NotesManager
from shipyard_airflow.common.notes.notes_helper import NotesHelper
from shipyard_airflow.common.notes.storage_impl_db import \
    ShipyardSQLNotesStorage

# Configuration sections
BASE = 'base'
K8S_LOGS = 'k8s_logs'
REQUESTS_CONFIG = 'requests_config'

LOG = logging.getLogger(__name__)


class UcpBaseOperator(BaseOperator):

    """Airship Base Operator

    All Airship related workflow operators will use the Airship base
    operator as the parent and inherit attributes and methods
    from this class

    """

    @apply_defaults
    def __init__(self,
                 main_dag_name=None,
                 pod_selector_pattern=None,
                 shipyard_conf=None,
                 start_time=None,
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
        :param xcom_push: xcom usage

        """

        super(UcpBaseOperator, self).__init__(*args, **kwargs)
        self.continue_processing = True
        self.main_dag_name = main_dag_name
        self.pod_selector_pattern = pod_selector_pattern or []
        self.shipyard_conf = shipyard_conf
        self.start_time = datetime.now()
        self.xcom_push_flag = xcom_push
        # lazy init field to hold a shipyard_db_engine
        self._shipyard_db_engine = None

    def execute(self, context):
        # Setup values that depend on the shipyard configuration
        self.doc_utils = _get_document_util(self.shipyard_conf)
        self.endpoints = service_endpoint.ServiceEndpoints(self.shipyard_conf)

        # Read and parse shiyard.conf
        self.config = configparser.ConfigParser()
        self.config.read(self.shipyard_conf)

        # Execute Airship base function
        self.ucp_base(context)

        # Execute base function for child operator
        self.run_base(context)

        if self.continue_processing:
            # Execute child function
            try:
                self.do_execute()
            except Exception:
                LOG.exception(
                    'Exception happened during %s execution, '
                    'will try to log additional details',
                    self.__class__.__name__)
                self.get_k8s_logs()
                if hasattr(self, 'fetch_failure_details'):
                    self.fetch_failure_details()
                raise

    def ucp_base(self, context):

        LOG.info("Running Airship Base Operator...")

        # Configure the notes helper for this run of an operator
        # establishes self.notes_helper
        self._setup_notes_helper()

        # Initialize variable that indicates the kubernetes namespace for the
        # Airship components
        self.ucp_namespace = self.config.get(K8S_LOGS, 'ucp_namespace')

        # Define task_instance
        self.task_instance = context['task_instance']

        # Set up and retrieve values from xcom
        self.xcom_puller = XcomPuller(self.main_dag_name, self.task_instance)
        self.action_info = self.xcom_puller.get_action_info()
        self.action_type = self.xcom_puller.get_action_type()
        self.dc = self.xcom_puller.get_deployment_configuration()

        # Set up other common-use values
        self.action_id = self.action_info['id']
        # extract the `task` or `step` name for easy access
        self.task_id = self.task_instance.task_id
        self.revision_id = self.action_info['committed_rev_id']
        self.action_params = self.action_info.get('parameters', {})
        self.context_marker = self.action_info['context_marker']
        self.user = self.action_info['user']
        self.design_ref = self._deckhand_design_ref()
        self._setup_target_nodes()

    def get_k8s_logs(self):
        """Retrieve Kubernetes pod/container logs specified by an operator

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

    def _setup_target_nodes(self):
        """Sets up the target nodes field for this action

        When managing a targeted action, this step needs to resolve the
        target node. If there are no targets found (should be caught before
        invocation of the DAG), then raise an exception so that it does not
        try to take action on more nodes than targeted.
        Later, when creating the deployment group, if this value
        (self.target_nodes) is set, it will be used in lieu of the design
        based deployment strategy.
        target_nodes will be a comma separated string provided as part of the
        parameters to an action on input to Shipyard.
        """
        if self.action_type == 'targeted':
            t_nodes = self.action_params.get('target_nodes', '')
            self.target_nodes = [n.strip() for n in t_nodes.split(',')]
            if not self.target_nodes:
                raise AirflowException(
                    '{} ({}) requires targeted nodes, but was unable to '
                    'resolve any targets in {}'.format(
                        self.main_dag_name, self.action_id,
                        self.__class__.__name__
                    )
                )
            LOG.info("Target Nodes for action: [%s]",
                     ', '.join(self.target_nodes))
        else:
            self.target_nodes = None

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

    def _get_shipyard_db_engine(self):
        """Lazy initialize an engine for the Shipyard database.

        :returns: a SQLAlchemy engine for the Shipyard database.

        Developer's Note: Initially the idea was to use the PostgresHook and
        retrieve an engine from there as is done with the concurrency check,
        but since we have easy access to a configuration file, this does
        direct SQLAlchemy to get the engine. By using the config, the database
        connection is not exposed as environment variables -- which is one way
        that Airflow registers database connections for use by the dbApiHook
        """
        if self._shipyard_db_engine is None:
            connection_string = self.config.get(BASE, 'postgresql_db')
            pool_size = self.config.getint(BASE, 'pool_size')
            max_overflow = self.config.getint(BASE, 'pool_overflow')
            pool_pre_ping = self.config.getboolean(BASE, 'pool_pre_ping')
            pool_recycle = self.config.getint(BASE, 'connection_recycle')
            pool_timeout = self.config.getint(BASE, 'pool_timeout')
            self._shipyard_db_engine = sqlalchemy.create_engine(
                connection_string, pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=pool_pre_ping,
                pool_recycle=pool_recycle,
                pool_timeout=pool_timeout
            )
            LOG.info("Initialized Shipyard database connection with pool "
                     "size: %d, max overflow: %d, pool pre ping: %s, pool "
                     "recycle: %d, and pool timeout: %d",
                     pool_size, max_overflow,
                     pool_pre_ping, pool_recycle,
                     pool_timeout)

        return self._shipyard_db_engine

    @shipyard_service_token
    def _token_getter(self):
        # Generator method to get a shipyard service token
        return self.svc_token

    def _setup_notes_helper(self):
        """Setup a notes helper for use by all descendent operators"""
        connect_timeout = self.config.get(REQUESTS_CONFIG,
                                          'notes_connect_timeout')
        read_timeout = self.config.get(REQUESTS_CONFIG, 'notes_read_timeout')
        self.notes_helper = NotesHelper(
            NotesManager(
                storage=ShipyardSQLNotesStorage(self._get_shipyard_db_engine),
                get_token=self._token_getter,
                connect_timeout=connect_timeout,
                read_timeout=read_timeout))


def _get_document_util(shipyard_conf):
    """Retrieve an instance of the DocumentValidationUtils"""
    dh_client = DeckhandClientFactory(shipyard_conf).get_client()
    return DocumentValidationUtils(dh_client)


class UcpBaseOperatorPlugin(AirflowPlugin):
    """Creates UcpBaseOperator in Airflow."""
    name = 'ucp_base_operator_plugin'
    operators = [UcpBaseOperator]
