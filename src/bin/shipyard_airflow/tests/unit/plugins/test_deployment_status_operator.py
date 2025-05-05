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
from unittest import mock, TestCase
import yaml

import kubernetes

import airflow
import pendulum
from shipyard_airflow.common.document_validators import \
    document_validation_utils
from shipyard_airflow.common.document_validators import errors
from shipyard_airflow.plugins import deckhand_client_factory
from shipyard_airflow.plugins import deployment_status_operator
from shipyard_airflow.plugins import xcom_puller
from airflow.sdk import DAG
from airflow.models import TaskInstance, DagRun
from airflow.utils.state import State
from airflow.utils.types import DagRunType

# @mock.patch.object(airflow.models.BaseOperator, '__init__')
class TestDeploymentStatusOperator(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestDeploymentStatusOperator, self).__init__(*args, **kwargs)
        self.status = {'status': "doc"}
        self.revision_id = "revision_id"
        self.version = {'version': "doc"}
        full_data = {
            'deployment': self.status,
            **self.version
        }
        self.config_map_data = {'release': yaml.safe_dump(full_data)}

    def setUp(self):
        # Create a DAG for the test using pendulum
        self.dag = DAG(dag_id="example_dag", start_date=pendulum.now('UTC').add(days=-1))

        # Create a DagRun to associate with the TaskInstance
        self.dag_run = DagRun(
            dag_id=self.dag.dag_id,
            logical_date=pendulum.now('UTC').add(days=-1),  # Use pendulum for execution_date
            run_id="manual__" + pendulum.now('UTC').to_iso8601_string(),
            run_type=DagRunType.MANUAL,
            state=State.RUNNING
        )

        # Create a TaskInstance with run_id
        self.operator = deployment_status_operator.DeploymentStatusOperator(
            shipyard_conf='conf', main_dag_name='name', dag=self.dag, task_id="task")

        self.task_instance = TaskInstance(task=self.operator, run_id=self.dag_run.run_id)
        self.task_instance.dag_run = self.dag_run  # Associate TaskInstance with DagRun
        self.task_instance.state = State.RUNNING

        # Set the context to include TaskInstance
        self.context = {'ti': self.task_instance}

    @mock.patch.object(deployment_status_operator.XcomPuller, 'get_concurrency_status', return_value=True)
    @mock.patch('shipyard_airflow.conf.config.parse_args')
    @mock.patch.object(deployment_status_operator.DeploymentStatusOperator, '_get_version_doc')
    @mock.patch.object(deployment_status_operator.DeploymentStatusOperator, '_get_status_and_revision')
    @mock.patch.object(deployment_status_operator.DeploymentStatusOperator, '_store_as_config_map')
    def test_execute(self,
                     store_as_config_map,
                     get_status_and_revision,
                     get_version_doc,
                     config_parse_args,
                     get_concurrency_status_mock):

        # Mock return values for the methods
        get_status_and_revision.return_value = (self.status, self.revision_id)
        get_version_doc.return_value = self.version

        # Execute the operator
        self.operator.execute(self.context)

        assert config_parse_args.called
        assert get_concurrency_status_mock.called
        assert get_status_and_revision.called
        get_version_doc.assert_called_once_with(self.revision_id)
        store_as_config_map.assert_called_once_with(self.config_map_data)

    @mock.patch.object(xcom_puller.XcomPuller, 'get_concurrency_status',
                       return_value=False)
    @mock.patch('shipyard_airflow.conf.config.parse_args')
    def test_execute_concurrency_fail(self,
                                      config_parse_args,
                                      xcom_puller):

        try:
            self.operator.execute(self.context)
        except airflow.AirflowException as err:
            assert str(err) == "Concurrency check did not pass, so the " \
                               "deployment status will not be updated"
        assert config_parse_args.called
        assert xcom_puller.called

    @mock.patch.object(kubernetes.config, 'load_incluster_config')
    @mock.patch.object(kubernetes.client.CoreV1Api,
                       'patch_namespaced_config_map')
    @mock.patch.object(kubernetes.client.CoreV1Api,
                       'create_namespaced_config_map')
    @mock.patch.object(deployment_status_operator.DeploymentStatusOperator,
                       '_create_config_map_object',
                       return_value='cfg_map_object')
    @mock.patch.object(configparser.ConfigParser, 'get', return_value="test")
    def test__store_as_config_map_map_does_not_exist(self,
                                                     config_parser,
                                                     create_cfg_map_object,
                                                     create_cfg_map,
                                                     patch_cfg_map,
                                                     load_k8s_config):
        data = 'data'

        patch_cfg_map.side_effect = kubernetes.client.rest.ApiException(
            status=404)

        self.operator._store_as_config_map(data)
        patch_cfg_map.assert_called_once_with(
            config_parser.return_value,
            config_parser.return_value,
            create_cfg_map_object.return_value,
            pretty=deployment_status_operator.CONFIG_MAP_DETAILS['pretty']
        )

        create_cfg_map_object.assert_called_once_with(
            config_parser.return_value, config_parser.return_value, data)
        create_cfg_map.assert_called_once_with(
            config_parser.return_value,
            create_cfg_map_object.return_value,
            pretty=deployment_status_operator.CONFIG_MAP_DETAILS['pretty'])

    @mock.patch('shipyard_airflow.plugins.deployment_status_operator'
                '.get_deployment_status')
    @mock.patch.object(kubernetes.config, 'load_incluster_config')
    @mock.patch.object(kubernetes.client.CoreV1Api,
                       'patch_namespaced_config_map')
    @mock.patch.object(kubernetes.client.CoreV1Api,
                       'create_namespaced_config_map')
    @mock.patch.object(deployment_status_operator.DeploymentStatusOperator,
                       '_create_config_map_object',
                       return_value='cfg_map_object')
    @mock.patch.object(configparser.ConfigParser, 'get', return_value="test")
    def test__store_as_config_map_map_already_exists(self,
                                                     config_parser,
                                                     create_cfg_map_object,
                                                     create_cfg_map,
                                                     patch_cfg_map,
                                                     load_k8s_config,
                                                     get_deployment_status):
        data = 'data'


        self.operator._store_as_config_map(data)
        patch_cfg_map.assert_called_once_with(
            config_parser.return_value,
            config_parser.return_value,
            create_cfg_map_object.return_value,
            pretty=deployment_status_operator.CONFIG_MAP_DETAILS['pretty']
        )

        create_cfg_map_object.assert_called_once_with(
            config_parser.return_value, config_parser.return_value, data)
        assert not create_cfg_map.called

    @mock.patch.object(kubernetes.config, 'load_incluster_config')
    @mock.patch.object(kubernetes.client.CoreV1Api,
                       'patch_namespaced_config_map')
    @mock.patch.object(deployment_status_operator.DeploymentStatusOperator,
                       '_create_config_map_object',
                       return_value='cfg_map_object')
    @mock.patch.object(configparser.ConfigParser, 'get', return_value="test")
    def test__store_as_config_map_bad_exception(self,
                                                config_parser,
                                                create_cfg_map_object,
                                                patch_cfg_map,
                                                load_k8s_config):
        data = 'data'

        patch_cfg_map.side_effect = kubernetes.client.rest.ApiException(
            status=409)

        try:
            self.operator._store_as_config_map(data)
        except kubernetes.client.rest.ApiException as err:
            assert patch_cfg_map.side_effect == err

        patch_cfg_map.assert_called_once_with(
            config_parser.return_value,
            config_parser.return_value,
            create_cfg_map_object.return_value,
            pretty=deployment_status_operator.CONFIG_MAP_DETAILS['pretty']
        )

        create_cfg_map_object.assert_called_once_with(
            config_parser.return_value, config_parser.return_value, data)

    @mock.patch.object(deckhand_client_factory.DeckhandClientFactory,
                       'get_client',
                       return_value="get_client")
    @mock.patch.object(document_validation_utils.DocumentValidationUtils,
                       'get_unique_doc',
                       return_value="get_unique_doc")
    @mock.patch.object(configparser.ConfigParser, 'get', return_value="test")
    def test__get_version_doc(self,
                              config_parser,
                              get_unique_doc,
                              get_client):

        result = self.operator._get_version_doc(self.revision_id)

        assert result == get_unique_doc.return_value
        assert get_client.called
        get_unique_doc.assert_called_once_with(
            revision_id=self.revision_id,
            schema=config_parser.return_value,
            name=config_parser.return_value)

    @mock.patch.object(deckhand_client_factory.DeckhandClientFactory,
                       'get_client',
                       return_value="get_client")
    @mock.patch.object(document_validation_utils.DocumentValidationUtils,
                       'get_unique_doc',
                       return_value="get_unique_doc")
    @mock.patch.object(configparser.ConfigParser, 'get', return_value="test")
    def test__get_version_doc_does_not_exist(self,
                                             config_parser,
                                             get_unique_doc,
                                             get_client):
        get_unique_doc.side_effect = errors.DocumentNotFoundError()


        result = self.operator._get_version_doc(self.revision_id)

        assert result == {}
        assert get_client.called
        get_unique_doc.assert_called_once_with(
            revision_id=self.revision_id,
            schema=config_parser.return_value,
            name=config_parser.return_value)

    @mock.patch('shipyard_airflow.plugins.deployment_status_operator'
                '.get_deployment_status')
    def test__get_status_and_revision(self,
                                      get_deployment_status):

        action = {'committed_rev_id': self.revision_id}
        self.operator.xcom_puller = mock.MagicMock()
        self.operator.xcom_puller.get_action_info = mock.MagicMock()
        self.operator.xcom_puller.get_action_info.return_value = action

        status_and_revision = self.operator._get_status_and_revision()

        get_deployment_status.assert_called_once_with(
            action,
            force_completed=self.operator.force_completed)

        assert status_and_revision == (get_deployment_status.return_value,
                                       self.revision_id)


class TestDeploymentStatusOperatorStatic:

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api', return_value='output')
    def test__get_k8s_client(self, client_create, load_config):
        operator_class = deployment_status_operator.DeploymentStatusOperator
        assert operator_class._get_k8s_client() == 'output'
        assert client_create.called
        assert load_config.called

    @mock.patch('shipyard_airflow.plugins.deployment_status_operator.'
                'V1ObjectMeta', return_value='meta_output')
    @mock.patch('shipyard_airflow.plugins.deployment_status_operator.'
                'V1ConfigMap', return_value='cfg_map_output')
    def test__create_config_map_object(self,
                                       config_map_create,
                                       metadata_create):
        data = 'data'
        name = 'name'
        namespace = 'namespace'
        operator_class = deployment_status_operator.DeploymentStatusOperator
        output = operator_class._create_config_map_object(
            name=name,
            namespace=namespace,
            data=data)
        assert output == 'cfg_map_output'
        config_map_create.assert_called_once_with(
           api_version=deployment_status_operator
           .CONFIG_MAP_DETAILS['api_version'],
           kind=deployment_status_operator.CONFIG_MAP_DETAILS['kind'],
           data=data,
           metadata='meta_output')
        metadata_create.assert_called_once_with(
           name=name,
           namespace=namespace)
