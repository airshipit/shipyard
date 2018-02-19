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
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin
from airflow.hooks.postgres_hook import PostgresHook
from airflow.exceptions import AirflowException

# constants related to the dag_run table.
DAG_RUN_SELECT_RUNNING_SQL = ("select dag_id, execution_date "
                              "from dag_run "
                              "where state='running'")

# connection name for airflow's own sql db
AIRFLOW_DB = 'airflows_own_db'

# each set in this list of sets indicates DAGs that shouldn't execute together
CONFLICTING_DAG_SETS = [set(['deploy_site', 'update_site', 'redeploy_server'])]


def find_conflicting_dag_set(dag_name, conflicting_dag_sets=None):
    """
    Using dag_name, finds all other dag names that are in any set of
    conflicting dags from input conflicting_dag_sets
    """
    if conflicting_dag_sets is None:
        conflicting_dag_sets = CONFLICTING_DAG_SETS
    full_set = set()
    for single_set in conflicting_dag_sets:
        if dag_name in single_set:
            full_set = full_set | single_set
    full_set.discard(dag_name)
    logging.info('Potential conflicts: %s', ', '.join(full_set))
    return full_set


class ConcurrencyCheckOperator(BaseOperator):
    """
    Provides a way to indicate which DAGs should not be executing
    simultaneously.
    """

    @apply_defaults
    def __init__(self, conflicting_dag_set=None, *args, **kwargs):
        super(ConcurrencyCheckOperator, self).__init__(*args, **kwargs)
        self.conflicting_dag_set = conflicting_dag_set

    def execute(self, context):
        """
        Run the check to see if this DAG has an concurrency issues with other
        DAGs. Stop the workflow if there is.
        """
        if self.conflicting_dag_set is None:
            self.check_dag_id = self.dag.dag_id
            logging.debug('dag_id is %s', self.check_dag_id)
            if '.' in self.dag.dag_id:
                self.check_dag_id = self.dag.dag_id.split('.', 1)[0]
                logging.debug('dag_id modified to %s', self.check_dag_id)

            logging.info('from dag %s, assuming %s for concurrency check',
                         self.dag.dag_id, self.check_dag_id)
            self.conflicting_dag_set = find_conflicting_dag_set(
                self.check_dag_id)

        logging.info('Checking for running of dags: %s',
                     ', '.join(self.conflicting_dag_set))

        conflicting_dag = self.find_conflicting_dag(self.check_dag_id)
        if conflicting_dag is None:
            logging.info('No conflicts found. Continuing Execution')
        else:
            self.abort_conflict(
                dag_name=self.check_dag_id, conflict=conflicting_dag)

    def get_executing_dags(self):
        """
        Encapsulation of getting database records of running dags.
        Returns a list of records of dag_id and execution_date
        """
        logging.info('Executing: %s', DAG_RUN_SELECT_RUNNING_SQL)
        airflow_pg_hook = PostgresHook(postgres_conn_id=AIRFLOW_DB)
        return airflow_pg_hook.get_records(DAG_RUN_SELECT_RUNNING_SQL)

    def find_conflicting_dag(self, dag_id_to_check):
        """
        Checks for a DAGs that is conflicting and exits based on the first
        one found.
        Also will return the dag_id_to_check as conflicting if more than 1
        instance is running
        """
        self_dag_count = 0
        for dag_id, execution_date in self.get_executing_dags():
            logging.info('Checking %s @ %s vs. current %s', dag_id,
                         execution_date, dag_id_to_check)
            if dag_id == dag_id_to_check:
                self_dag_count += 1
                logging.info(
                    "Found an instance of the dag_id being checked. Tally: %s",
                    self_dag_count)
            if dag_id in self.conflicting_dag_set:
                logging.info("Conflict found: %s @ %s", dag_id, execution_date)
                return dag_id
        if self_dag_count > 1:
            return dag_id_to_check
        return None

    def abort_conflict(self, dag_name, conflict):
        """
        Log and raise an exception that there is a conflicting workflow.
        """
        conflict_string = '{} conflicts with running {}. Aborting run'.format(
            dag_name, conflict)
        logging.error(conflict_string)
        raise AirflowException(conflict_string)


class ConcurrencyCheckPlugin(AirflowPlugin):
    """
    Register this plugin for this operator.
    """
    name = 'concurrency_check_operator_plugin'
    operators = [ConcurrencyCheckOperator]
