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
from airflow.operators import ConcurrencyCheckOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator

from armada_deploy_site import deploy_site_armada
import dag_names as dn
from deckhand_get_design import get_design_deckhand
from destroy_node import destroy_server
from drydock_deploy_site import deploy_site_drydock
from failure_handlers import step_failure_handler
from dag_deployment_configuration import get_deployment_configuration
from preflight_checks import all_preflight_checks
from validate_site_design import validate_site_design


class CommonStepFactory(object):
    """Common step factory

    A factory to generate steps that are reused among multiple dags
    """
    def __init__(self, parent_dag_name, dag, default_args):
        """Creates a factory

        Uses the specified parent_dag_name
        """
        self.parent_dag_name = parent_dag_name
        self.dag = dag
        self.default_args = default_args

    def get_action_xcom(self, task_id=dn.ACTION_XCOM):
        """Generate the action_xcom step

        Step responsible for getting the action information passed
        by the invocation of the dag, which includes any options.
        """
        def xcom_push(**kwargs):
            """xcom_push function

            Defines a push function to store the content of 'action' that is
            defined via 'dag_run' in XCOM so that it can be used by the
            Operators
            """

            kwargs['ti'].xcom_push(key='action',
                                   value=kwargs['dag_run'].conf['action'])

        return PythonOperator(task_id=task_id,
                              dag=self.dag,
                              python_callable=xcom_push)

    def get_concurrency_check(self, task_id=dn.DAG_CONCURRENCY_CHECK_DAG_NAME):
        """Generate the concurrency check step

        Concurrency check prevents simultaneous execution of dags that should
        not execute together.
        """
        return ConcurrencyCheckOperator(
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_preflight(self, task_id=dn.ALL_PREFLIGHT_CHECKS_DAG_NAME):
        """Generate the preflight step

        Preflight checks preconditions for running a DAG
        """
        return SubDagOperator(
            subdag=all_preflight_checks(
                self.parent_dag_name,
                task_id,
                args=self.default_args),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_get_design_version(self, task_id=dn.DECKHAND_GET_DESIGN_VERSION):
        """Generate the get design version step

        Retrieves the version of the design to use from deckhand
        """
        return SubDagOperator(
            subdag=get_design_deckhand(
                self.parent_dag_name,
                task_id,
                args=self.default_args),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_validate_site_design(self,
                                 task_id=dn.VALIDATE_SITE_DESIGN_DAG_NAME):
        """Generate the validate site design step

        Validation of the site design checks that the design to be used
        for a deployment passes checks before using it.
        """
        return SubDagOperator(
            subdag=validate_site_design(
                self.parent_dag_name,
                task_id,
                args=self.default_args),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_deployment_configuration(self,
                                     task_id=dn.GET_DEPLOY_CONF_DAG_NAME):
        """Generate the step to retrieve the deployment configuration

        This step provides the timings and strategies that will be used in
        subsequent steps
        """
        return SubDagOperator(
            subdag=get_deployment_configuration(
                self.parent_dag_name,
                task_id,
                args=self.default_args),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_drydock_build(self, task_id=dn.DRYDOCK_BUILD_DAG_NAME):
        """Generate the drydock build step

        Drydock build does the hardware provisioning.
        """
        return SubDagOperator(
            subdag=deploy_site_drydock(
                self.parent_dag_name,
                task_id,
                args=self.default_args),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_armada_build(self, task_id=dn.ARMADA_BUILD_DAG_NAME):
        """Generate the armada build step

        Armada build does the deployment of helm charts
        """
        return SubDagOperator(
            subdag=deploy_site_armada(
                self.parent_dag_name,
                task_id,
                args=self.default_args),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_destroy_server(self, task_id=dn.DESTROY_SERVER_DAG_NAME):
        """Generate a destroy server step

        Destroy server tears down kubernetes and hardware
        """
        return SubDagOperator(
            subdag=destroy_server(
                self.parent_dag_name,
                task_id,
                args=self.default_args),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)
