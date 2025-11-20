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
from configparser import ConfigParser
from unittest import mock

import pytest
import yaml

import airflow
from airflow.exceptions import AirflowException

ACTION_INFO = {
    'committed_rev_id': 2,
    'dag_id': 'deploy_site',
    'id': '01CBGWY1GXQVXVCXRJKM9V71AT',
    'name': 'deploy_site',
    'parameters': {},
    'timestamp': '2018-04-20 06:47:43.905047',
    'user': 'shipyard'}

ACTION_INFO_NO_COMMIT = {
    'committed_rev_id': None,
    'dag_id': 'deploy_site',
    'id': '01CBGWY1GXQVXVCXRJKM9V71AT',
    'name': 'deploy_site',
    'parameters': {},
    'timestamp': '2018-04-20 06:47:43.905047',
    'user': 'shipyard'}


try:
    from deployment_configuration_operator import (
        DeploymentConfigurationOperator,
        DOCUMENT_INFO
    )
except ImportError:
    from shipyard_airflow.plugins.deployment_configuration_operator import (
        DeploymentConfigurationOperator,
        DOCUMENT_INFO
    )

try:
    from deckhand_client_factory import DeckhandClientFactory
except ImportError:
    from shipyard_airflow.plugins.deckhand_client_factory import (
        DeckhandClientFactory
    )


def make_fake_config():
    """Make/return a fake config using configparser that we can use for testing

    :returns: A fake configuration object
    :rtype: ConfigParser
    """
    cfg = ConfigParser()
    cfg.add_section(DOCUMENT_INFO)
    cfg.set(DOCUMENT_INFO, 'deployment_configuration_name',
            'deployment-configuration')
    cfg.set(DOCUMENT_INFO, 'deployment_configuration_schema',
            'shipyard/DeploymentConfiguration/v1')
    return cfg


def test_execute_exception():
    """Test that execute results in a failure with bad context"""

    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    with pytest.raises(AirflowException) as expected_exc:
        # Design revision is not set on xcom pull
        dco.execute(context={})
    assert ("Design_revision is not set. Cannot proceed with retrieval"
            " of the design configuration") in str(expected_exc)

@mock.patch.object(DeploymentConfigurationOperator, '_read_config')
@mock.patch.object(DeploymentConfigurationOperator, 'get_revision_id',
                   return_value=99)
def test_execute_no_client(get_revision_id, read_config):
    # no keystone authtoken present in configuration
    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    dco.config = make_fake_config()
    with pytest.raises(AirflowException) as expected_exc:
        dco.execute(context={'task_instance': 'asdf'})
    assert ("Failed to retrieve deployment-configuration yaml") in str(
        expected_exc)
    get_revision_id.assert_called_once_with('asdf')
    read_config.assert_called_once_with()


def test_get_revision_id():
    """Test that get revision id follows desired exits"""
    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    ti = mock.MagicMock(spec=airflow.models.TaskInstance)
    ti.xcom_pull.return_value = ACTION_INFO
    rid = dco.get_revision_id(ti)
    assert rid == 2


def test_get_revision_id_none():
    """Test that get revision id follows desired exits"""
    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    ti = mock.MagicMock(spec=airflow.models.TaskInstance)
    ti.xcom_pull.return_value = ACTION_INFO_NO_COMMIT
    with pytest.raises(AirflowException) as expected_exc:
        rid = dco.get_revision_id(ti)
    assert "Design_revision is not set." in str(expected_exc)


def test_get_doc_no_deckhand():
    """Get doc should fail to contact deckhand return a document"""
    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    dco.config = make_fake_config()
    with pytest.raises(AirflowException) as expected_exc:
        dco.get_doc(99)
    assert "Failed to retrieve deployment" in str(expected_exc)


def get_m_client(data):
    doc_obj = mock.MagicMock()
    doc_obj.data = data
    doc_obj_l = [doc_obj]
    mock_client = mock.MagicMock()
    mock_client.revisions.documents = lambda r, rendered, **filters: doc_obj_l
    return mock_client


@mock.patch.object(DeckhandClientFactory, 'get_client',
                   return_value=get_m_client('abcdefg'))
def test_get_doc_mock_deckhand(*args):
    """Get doc should return a document"""
    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    dco.config = make_fake_config()
    doc = dco.get_doc(99)
    assert doc == 'abcdefg'


@mock.patch.object(DeckhandClientFactory, 'get_client',
                   return_value=get_m_client(None))
def test_get_doc_mock_deckhand_invalid(*args):
    """Get doc should return a document"""
    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    dco.config = make_fake_config()

    with pytest.raises(AirflowException) as airflow_ex:
        dco.get_doc(99)
    assert 'valid deployment-configuration' in str(airflow_ex)


sample_deployment_config = """
  physical_provisioner:
    deployment_strategy: all-at-once
    deploy_interval: 900
  kubernetes_provisioner:
    drain_timeout: 3600
    drain_grace_period: 1800
    clear_labels_timeout: 1800
    remove_etcd_timeout: 1800
    etcd_ready_timeout: 600
  armada:
    manifest: 'full-site'"""


def test_map_config_keys():
    """Should reutrn the new dict from the yaml dict"""
    yaml_dict = yaml.safe_load(sample_deployment_config)
    dco = DeploymentConfigurationOperator(main_dag_name="main",
                                          shipyard_conf="shipyard.conf",
                                          task_id="t1")
    mapped = dco.map_config_keys(yaml_dict)
    for key in DeploymentConfigurationOperator.config_keys_defaults:
        assert key in mapped
    assert mapped.get("physical_provisioner.deploy_interval") == 900
    assert mapped.get("physical_provisioner.verify_timeout") == 60
