# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
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

import yaml
from airflow import AirflowException
from airflow.plugins_manager import AirflowPlugin
from airflow.sdk import BaseOperator
import kubernetes
from kubernetes.client.rest import ApiException
from kubernetes.client.models.v1_config_map import V1ConfigMap
from kubernetes.client.models.v1_object_meta import V1ObjectMeta

from shipyard_airflow.conf import config

from shipyard_airflow.control.helpers.action_helper import \
    get_deployment_status

from shipyard_airflow.plugins.xcom_puller import XcomPuller

from shipyard_airflow.common.document_validators.document_validation_utils \
    import DocumentValidationUtils
from shipyard_airflow.plugins.deckhand_client_factory import \
    DeckhandClientFactory

from shipyard_airflow.common.document_validators.errors import \
    DocumentNotFoundError

LOG = logging.getLogger(__name__)

# Variable to hold details about how the Kubernetes ConfigMap is stored
CONFIG_MAP_DETAILS = {
    'api_version': 'v1',
    'kind': 'ConfigMap',
    'pretty': 'true'
}


class DeploymentStatusOperator(BaseOperator):
    """Deployment status operator

    Update Kubernetes with the deployment status of this dag's action
    """

    def __init__(self,
                 shipyard_conf,
                 main_dag_name,
                 force_completed=False,
                 *args,
                 **kwargs):
        super(DeploymentStatusOperator, self).__init__(*args, **kwargs)
        self.shipyard_conf = shipyard_conf
        self.main_dag_name = main_dag_name
        self.force_completed = force_completed
        self.xcom_puller = None

    def execute(self, context):
        """Execute the main code for this operator.

        Create a ConfigMap with the deployment status of this dag's action
        """
        LOG.info("Running deployment status operator")

        self.xcom_puller = XcomPuller(self.main_dag_name, context['ti'])

        # Required for the get_deployment_status helper to function properly
        config.parse_args(args=[], default_config_files=[self.shipyard_conf])

        # First we need to check if the concurrency check was successful as
        # this operator is expected to run even if upstream steps fail
        if not self.xcom_puller.get_concurrency_status():
            msg = "Concurrency check did not pass, so the deployment status " \
                  "will not be updated"
            LOG.error(msg)
            raise AirflowException(msg)

        deployment_status_doc, revision_id = self._get_status_and_revision()
        deployment_version_doc = self._get_version_doc(revision_id)

        full_data = {
            'deployment': deployment_status_doc,
            **deployment_version_doc
        }
        config_map_data = {'release': yaml.safe_dump(full_data)}

        self._store_as_config_map(config_map_data)

    def _get_status_and_revision(self):
        """Retrieve the deployment status information from the appropriate
        helper function

        :return: dict with the status of the deployment
        :return: revision_id of the action
        """
        action_info = self.xcom_puller.get_action_info()
        deployment_status = get_deployment_status(
            action_info, force_completed=self.force_completed)

        revision_id = action_info['committed_rev_id']

        return deployment_status, revision_id

    def _get_version_doc(self, revision_id):
        """Retrieve the deployment-version document from Deckhand

        :param revision_id: the revision_id of the docs to grab the
                            deployment-version document from
        :return: deployment-version document returned from Deckhand
        """
        # Read and parse shipyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        doc_name = config.get('document_info', 'deployment_version_name')
        doc_schema = config.get('document_info', 'deployment_version_schema')

        dh_client = DeckhandClientFactory(self.shipyard_conf).get_client()
        dh_tool = DocumentValidationUtils(dh_client)

        try:
            deployment_version_doc = dh_tool.get_unique_doc(
                revision_id=revision_id, schema=doc_schema, name=doc_name)
            return deployment_version_doc
        except DocumentNotFoundError:
            LOG.info("There is no deployment-version document in Deckhand "
                     "under the revision '{}' with the name '{}' and schema "
                     "'{}'".format(revision_id, doc_name, doc_schema))
            return {}

    def _store_as_config_map(self, data):
        """Store given data in a Kubernetes ConfigMap

        :param dict data: The data to store in the ConfigMap
        """
        LOG.info("Storing deployment status as Kubernetes ConfigMap")
        # Read and parse shipyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        name = config.get('deployment_status_configmap', 'name')
        namespace = config.get('deployment_status_configmap', 'namespace')

        k8s_client = self._get_k8s_client()

        cfg_map_obj = self._create_config_map_object(name, namespace, data)
        cfg_map_naming = "(name: {}, namespace: {})".format(name, namespace)
        try:
            LOG.info("Updating deployment status config map {}, ".format(
                cfg_map_naming))
            k8s_client.patch_namespaced_config_map(
                name,
                namespace,
                cfg_map_obj,
                pretty=CONFIG_MAP_DETAILS['pretty'])
        except ApiException as err:
            if err.status != 404:
                raise
            # ConfigMap still needs to be created
            LOG.info("Deployment status config map does not exist yet")
            LOG.info("Creating deployment status config map {}".format(
                cfg_map_naming))
            k8s_client.create_namespaced_config_map(
                namespace, cfg_map_obj, pretty=CONFIG_MAP_DETAILS['pretty'])

    @staticmethod
    def _get_k8s_client():
        """Create and return a Kubernetes client

        :returns: A Kubernetes client object
        :rtype: kubernetes.client
        """
        # Note that we are using 'in_cluster_config'
        LOG.debug("Loading Kubernetes config")
        kubernetes.config.load_incluster_config()
        LOG.debug("Creating Kubernetes client")
        return kubernetes.client.CoreV1Api()

    @staticmethod
    def _create_config_map_object(name, namespace, data):
        """Create/return a Kubernetes ConfigMap object out of the given data

        :param dict data: The data to put into the config map
        :returns: A config map object made from the given data
        :rtype: V1ConfigMap
        """
        LOG.debug("Creating Kubernetes config map object")
        metadata = V1ObjectMeta(name=name, namespace=namespace)
        return V1ConfigMap(api_version=CONFIG_MAP_DETAILS['api_version'],
                           kind=CONFIG_MAP_DETAILS['kind'],
                           data=data,
                           metadata=metadata)


class DeploymentStatusOperatorPlugin(AirflowPlugin):
    """Creates DeploymentStatusOperatorPlugin in Airflow."""
    name = "deployment_status_operator"
    operators = [DeploymentStatusOperator]
