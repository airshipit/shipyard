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
"""Deployment Configuration

Retrieves the deployment-configuration from Deckhand and places the values
retrieved into a dictionary
"""
import configparser
import logging

from airflow.exceptions import AirflowException
from airflow.sdk import BaseOperator
from airflow.plugins_manager import AirflowPlugin

try:
    from deckhand_client_factory import DeckhandClientFactory
    from xcom_puller import XcomPuller
except ImportError:
    from shipyard_airflow.plugins.deckhand_client_factory import (
        DeckhandClientFactory)
    from shipyard_airflow.plugins.xcom_puller import XcomPuller
from shipyard_airflow.shipyard_const import CustomHeaders

LOG = logging.getLogger(__name__)
DOCUMENT_INFO = 'document_info'


class DeploymentConfigurationOperator(BaseOperator):
    """Deployment Configuration Operator

    Retrieve the deployment-configuration from Deckhand for use throughout
    the workflow. Put the configuration into a dictionary.

    Failures are raised:
      -  when Deckhand cannot be contacted
      -  when the DeploymentConfiguration (deployment-configuration) document
         cannot be retrieved
    """
    config_keys_defaults = {
        "physical_provisioner.deployment_strategy": None,
        "physical_provisioner.deploy_interval": 30,
        "physical_provisioner.deploy_timeout": 3600,
        "physical_provisioner.destroy_interval": 30,
        "physical_provisioner.destroy_timeout": 900,
        "physical_provisioner.join_wait": 120,
        "physical_provisioner.prepare_node_interval": 30,
        "physical_provisioner.prepare_node_timeout": 1800,
        "physical_provisioner.prepare_site_interval": 10,
        "physical_provisioner.prepare_site_timeout": 300,
        "physical_provisioner.verify_interval": 10,
        "physical_provisioner.verify_timeout": 60,
        "physical_provisioner.relabel_nodes_interval": 30,
        "physical_provisioner.relabel_nodes_timeout": 900,
        "kubernetes.node_status_interval": 30,
        "kubernetes.node_status_timeout": 1800,
        "kubernetes_provisioner.drain_timeout": 3600,
        "kubernetes_provisioner.drain_grace_period": 1800,
        "kubernetes_provisioner.clear_labels_timeout": 1800,
        "kubernetes_provisioner.remove_etcd_timeout": 1800,
        "kubernetes_provisioner.etcd_ready_timeout": 600,
        "armada.get_releases_timeout": 300,
        "armada.get_status_timeout": 300,
        "armada.manifest": "full-site",
        "armada.update_manifest": "full-site",
        "armada.post_apply_timeout": 2700,
        "armada.validate_design_timeout": 600
    }

    def __init__(self,
                 main_dag_name=None,
                 shipyard_conf=None,
                 *args,
                 **kwargs):
        """Deployment Configuration Operator

        Generate a DeploymentConfigurationOperator to read the deployment's
        configuration for use by other operators

        :param main_dag_name: Parent Dag
        :param shipyard_conf: Location of shipyard.conf
        """
        super(DeploymentConfigurationOperator, self).__init__(*args, **kwargs)
        self.main_dag_name = main_dag_name
        self.shipyard_conf = shipyard_conf
        self.action_info = {}

    def _read_config(self):
        """Read in and parse the shipyard config"""
        self.config = configparser.ConfigParser()
        self.config.read(self.shipyard_conf)

    def execute(self, context):
        """Perform Deployment Configuration extraction"""
        self._read_config()
        revision_id = self.get_revision_id(context.get('task_instance'))
        doc = self.get_doc(revision_id)
        converted = self.map_config_keys(doc)

        # return the mapped configuration so that it can be placed on xcom
        return converted

    def get_revision_id(self, task_instance):
        """Get the revision id from xcom"""
        if task_instance:
            LOG.debug("task_instance found, extracting design version")
            # Get XcomPuller instance
            self.xcom_puller = XcomPuller(self.main_dag_name, task_instance)
            # Set the revision_id to the revision on the xcom
            self.action_info = self.xcom_puller.get_action_info()

            revision_id = self.action_info['committed_rev_id']

            if revision_id:
                LOG.info("Revision is set to: %s for deployment-configuration",
                         revision_id)
                return revision_id
        # either revision id was not on xcom, or the task_instance is messed
        raise AirflowException(
            "Design_revision is not set. Cannot proceed with retrieval of"
            " the design configuration")

    def get_doc(self, revision_id):
        """Get the DeploymentConfiguration document dictionary from Deckhand"""
        schema_fallback = 'shipyard/DeploymentConfiguration/v1'
        schema = self.config.get(DOCUMENT_INFO,
                                 'deployment_configuration_schema',
                                 fallback=schema_fallback)
        name = self.config.get(DOCUMENT_INFO,
                               'deployment_configuration_name',
                               fallback='deployment-configuration')
        LOG.info("Attempting to retrieve {}, {} from Deckhand".format(
            schema, name))
        filters = {"schema": schema, "metadata.name": name}

        # Create additional headers dict to pass context marker
        # and end user
        addl_headers = None
        if self.action_info:
            context_marker = self.action_info['context_marker']
            end_user = self.action_info['user']
            addl_headers = {
                CustomHeaders.CONTEXT_MARKER.value: context_marker,
                CustomHeaders.END_USER.value: end_user
            }

        try:
            dhclient = DeckhandClientFactory(
                self.shipyard_conf).get_client(addl_headers=addl_headers)
            LOG.info("Deckhand Client acquired")
            doc = dhclient.revisions.documents(revision_id,
                                               rendered=True,
                                               **filters)
        except Exception as ex:
            try:
                failed_url = ex.url
            except AttributeError:
                failed_url = "No URL generated"
            LOG.exception(ex)
            raise AirflowException("Failed to retrieve deployment-"
                                   "configuration yaml using url: "
                                   "{}".format(failed_url))

        if len(doc) == 1 and doc[0].data:
            doc_dict = doc[0].data
        else:
            raise AirflowException("A valid deployment-configuration is "
                                   "required")

        LOG.info("DeploymentConfiguration retrieved")
        return doc_dict

    def map_config_keys(self, cfg_data):
        """Maps the deployment-configuration

        Converts to a more simple map of key-value pairs
        """
        LOG.info("Mapping keys from deployment-configuration")
        return {
            cfg_key: self.get_cfg_value(cfg_data, cfg_key, cfg_default)
            for cfg_key, cfg_default in
            DeploymentConfigurationOperator.config_keys_defaults.items()
        }

    def get_cfg_value(self, cfg_data, cfg_key, cfg_default):
        """Uses the dot notation key to get the value from the design config"""
        data = cfg_data
        for node in cfg_key.split('.'):
            data = data.get(node, {})
        if data:
            LOG.info("Deployment Config value set- %s: %s", cfg_key, data)
            return data
        else:
            LOG.info("Deployment Config using default- %s: %s", cfg_key,
                     cfg_default)
            return cfg_default


class DeploymentConfigurationOperatorPlugin(AirflowPlugin):
    name = 'deployment_configuration_operator_plugin'
    operators = [DeploymentConfigurationOperator]
