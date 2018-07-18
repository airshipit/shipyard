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
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator

try:
    # Operators are loaded from being registered to airflow.operators
    # in a deployed fashion
    from airflow.operators import ConcurrencyCheckOperator
    from airflow.operators import DeckhandRetrieveRenderedDocOperator
    from airflow.operators import DeploymentConfigurationOperator
    from airflow.operators import DeckhandCreateSiteActionTagOperator
    from airflow.operators import DrydockDestroyNodeOperator
except ImportError:
    # for local testing, they are loaded from their source directory
    from shipyard_airflow.plugins.concurrency_check_operator import \
        ConcurrencyCheckOperator
    from shipyard_airflow.plugins.deckhand_retrieve_rendered_doc import \
        DeckhandRetrieveRenderedDocOperator
    from shipyard_airflow.plugins.deployment_configuration_operator import \
        DeploymentConfigurationOperator
    from shipyard_airflow.plugins.deckhand_create_site_action_tag import \
        DeckhandCreateSiteActionTagOperator
    from shipyard_airflow.plugins.drydock_destroy_nodes import \
        DrydockDestroyNodeOperator

try:
    # modules reside in a flat directory when deployed with dags
    from armada_deploy_site import deploy_site_armada
    from config_path import config_path
    from destroy_node import destroy_server
    from drydock_deploy_site import deploy_site_drydock
    from failure_handlers import step_failure_handler
    from preflight_checks import all_preflight_checks
    from validate_site_design import validate_site_design
    import dag_names as dn
except ImportError:
    # for testing, specify the qualified source directory
    from shipyard_airflow.dags.armada_deploy_site import deploy_site_armada
    from shipyard_airflow.dags.config_path import config_path
    from shipyard_airflow.dags.destroy_node import destroy_server
    from shipyard_airflow.dags.drydock_deploy_site import deploy_site_drydock
    from shipyard_airflow.dags.failure_handlers import step_failure_handler
    from shipyard_airflow.dags.preflight_checks import all_preflight_checks
    from shipyard_airflow.dags.validate_site_design import validate_site_design
    import shipyard_airflow.dags.dag_names as dn


class CommonStepFactory(object):
    """Common step factory

    A factory to generate steps that are reused among multiple dags
    """
    def __init__(self, parent_dag_name, dag, default_args, action_type):
        """Creates a factory

        :param parent_dag_name: the name of the base DAG that this step
            factory will service
        :param dag: the dag object
        :param default_args: the default args from the dag that will be used
            by steps in lieu of overridden values.
        :action_type: defines the type of action - site, targeted, possibly
            others that will be stored on xcom if the action_xcom step is used.
            This can then be used to drive behavior in later steps.
        """
        self.parent_dag_name = parent_dag_name
        self.dag = dag
        self.default_args = default_args
        self.action_type = action_type or 'default'

    def get_action_xcom(self, task_id=dn.ACTION_XCOM):
        """Generate the action_xcom step

        Step responsible for getting the action information passed
        by the invocation of the dag, which includes any options.
        """
        def xcom_push(**kwargs):
            """xcom_push function

            Defines a push function to store the content of 'action' that is
            defined via 'dag_run' in XCOM so that it can be used by the
            Operators. Includes action-related information for later steps.
            """

            kwargs['ti'].xcom_push(key='action',
                                   value=kwargs['dag_run'].conf['action'])
            kwargs['ti'].xcom_push(key='action_type',
                                   value=self.action_type)

        return PythonOperator(task_id=task_id,
                              dag=self.dag,
                              python_callable=xcom_push)

    def get_concurrency_check(self, task_id=dn.CONCURRENCY_CHECK):
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

    def get_get_rendered_doc(self, task_id=dn.GET_RENDERED_DOC):
        """Generate the get deckhand rendered doc step

        Check that we are able to render the docs before proceeding
        further with the workflow
        """
        return DeckhandRetrieveRenderedDocOperator(
            shipyard_conf=config_path,
            main_dag_name=self.parent_dag_name,
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_validate_site_design(self,
                                 targets=None,
                                 task_id=dn.VALIDATE_SITE_DESIGN_DAG_NAME):
        """Generate the validate site design step

        Validation of the site design checks that the design to be used
        for a deployment passes checks before using it.
        """
        return SubDagOperator(
            subdag=validate_site_design(
                self.parent_dag_name,
                task_id,
                args=self.default_args,
                targets=targets),
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_deployment_configuration(self,
                                     task_id=dn.DEPLOYMENT_CONFIGURATION):
        """Generate the step to retrieve the deployment configuration

        This step provides the timings and strategies that will be used in
        subsequent steps
        """
        return DeploymentConfigurationOperator(
            main_dag_name=self.parent_dag_name,
            shipyard_conf=config_path,
            task_id=task_id,
            on_failure_callback=step_failure_handler,
            dag=self.dag)

    def get_drydock_build(self, task_id=dn.DRYDOCK_BUILD_DAG_NAME,
                          verify_nodes_exist=False):
        """Generate the drydock build step

        Drydock build does the hardware provisioning.
        """
        return SubDagOperator(
            subdag=deploy_site_drydock(
                self.parent_dag_name,
                task_id,
                args=self.default_args,
                verify_nodes_exist=verify_nodes_exist),
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

    def get_unguarded_destroy_servers(self, task_id=dn.DESTROY_SERVER):
        """Generates an unguarded destroy server step.

        This version of destroying servers does no pre-validations or extra
        shutdowns of anything. It unconditionally triggers Drydock to destroy
        the server. The counterpart to this step is the subdag returned by the
        get_destroy_server method below.
        """
        return DrydockDestroyNodeOperator(
            shipyard_conf=config_path,
            main_dag_name=self.parent_dag_name,
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

    def get_decide_airflow_upgrade(self, task_id=dn.DECIDE_AIRFLOW_UPGRADE):
        """Generate the decide_airflow_upgrade step

        Step responsible for deciding whether to branch to the path
        to upgrade airflow worker
        """
        def upgrade_airflow_check(**kwargs):
            """upgrade_airflow_check function

            Defines a function to decide whether to upgrade airflow
            worker. The decision will be based on the xcom value that
            is retrieved from the 'armada_post_apply' task
            """
            # DAG ID will be parent + subdag name
            dag_id = self.parent_dag_name + '.' + dn.ARMADA_BUILD_DAG_NAME

            # Check if Shipyard/Airflow were upgraded by the workflow
            upgrade_airflow = kwargs['ti'].xcom_pull(
                key='upgrade_airflow_worker',
                task_ids='armada_post_apply',
                dag_id=dag_id)

            # Go to the branch to upgrade Airflow worker if the Shipyard
            # chart were upgraded/modified
            if upgrade_airflow == "true":
                return "upgrade_airflow"
            else:
                return "skip_upgrade_airflow"

        return BranchPythonOperator(task_id=task_id,
                                    python_callable=upgrade_airflow_check,
                                    trigger_rule="all_success",
                                    dag=self.dag)

    def get_upgrade_airflow(self, task_id=dn.UPGRADE_AIRFLOW):
        """Generate the upgrade_airflow step

        Step responsible for upgrading airflow worker. Step will
        execute the upgrade script in the background and direct
        output to null so that 'nohup.out' will not be created.
        Note that this is done intentionally so that the upgrade
        of airflow worker will only start after the completion of
        the 'update_site' workflow. This will ensure availability
        of airflow worker during update/upgrade and prevent any
        disruption to the workflow. Note that dag_id and execution
        date are required for proper execution of the script.
        """
        return BashOperator(task_id=task_id,
                            bash_command=(
                                "nohup "
                                "/usr/local/airflow/upgrade_airflow_worker.sh "
                                "{{ ti.dag_id }} {{ ti.execution_date }} "
                                ">/dev/null 2>&1 &"),
                            dag=self.dag)

    def get_skip_upgrade_airflow(self, task_id=dn.SKIP_UPGRADE_AIRFLOW):
        """Generate the skip_upgrade_airflow step

        Step will print a message stating that we do not need to
        upgrade the airflow worker
        """
        return BashOperator(task_id=task_id,
                            bash_command=(
                                "echo 'Airflow Worker Upgrade Not Required'"),
                            dag=self.dag)

    def get_create_action_tag(self, task_id=dn.CREATE_ACTION_TAG):
        """Generate the create action tag step

        Step is responsible for tagging the revision with either
        'site-action-success' or 'site-action-failure' depending
        on the final state of the site action.

        Note that trigger_rule is set to "all_done" so that this
        step will run even when upstream tasks are in failed state.
        """

        return DeckhandCreateSiteActionTagOperator(
            task_id=task_id,
            shipyard_conf=config_path,
            on_failure_callback=step_failure_handler,
            trigger_rule="all_done",
            main_dag_name=self.parent_dag_name,
            dag=self.dag)
