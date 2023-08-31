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
"""
Airflow database access - see db.py for instances to use
"""
import sqlalchemy
from oslo_config import cfg

from shipyard_airflow.db.common_db import DbAccess
from shipyard_airflow.db.errors import AirflowStateError


CONF = cfg.CONF


class AirflowDbAccess(DbAccess):
    """
    Airflow database access
    WARNING: This is a large set of assumptions based on the way airflow
    arranges its database and are subject to change with airflow future
    releases - i.e. we're leveraging undocumented/non-exposed interfaces
    for airflow to work around lack of API and feature functionality.
    """

    SELECT_ALL_DAG_RUNS = sqlalchemy.sql.text('''
    SELECT
        "id",
        "dag_id",
        "state",
        "run_id",
        "execution_date",
        "external_trigger",
        "conf",
        "end_date",
        "start_date"
    FROM
        dag_run
    ''')

    SELECT_DAG_RUNS_BY_ID = sqlalchemy.sql.text('''
    SELECT
        "id",
        "dag_id",
        "state",
        "run_id",
        "execution_date",
        "external_trigger",
        "conf",
        "end_date",
        "start_date"
    FROM
        dag_run
    WHERE
        dag_id = :dag_id
    AND
        execution_date = :execution_date
    ''')

    # The like parameter must have '%' appropriately applied to the args
    # used to merge into this query.
    SELECT_DAG_RUNS_LIKE_ID = sqlalchemy.sql.text('''
    SELECT
        "id",
        "dag_id",
        "state",
        "run_id",
        "execution_date",
        "external_trigger",
        "conf",
        "end_date",
        "start_date"
    FROM
        dag_run
    WHERE
        dag_id LIKE :dag_id
    AND
        execution_date = :execution_date
    ''')

    SELECT_ALL_TASKS = sqlalchemy.sql.text('''
    SELECT
        "task_id",
        "dag_id",
        "execution_date",
        "dr"."run_id",
        "start_date",
        "end_date",
        "duration",
        "state",
        "try_number",
        "hostname",
        "unixname",
        "job_id",
        "pool",
        "queue",
        "priority_weight",
        "operator",
        "queued_dttm",
        "pid",
        "max_tries"
    FROM
        task_instance ti
    INNER JOIN
        (
            SELECT
                "execution_date",
                "run_id"
            FROM
                dag_run
            GROUP BY
                run_id,
                execution_date
        ) dr
    ON ti.run_id=dr.run_id
    ORDER BY
        priority_weight desc,
        start_date
    ''')

    # The like parameter must have '%' appropriately applied to the args
    # used to merge into this query.
    SELECT_TASKS_BY_ID = sqlalchemy.sql.text('''
    SELECT
            "task_id",
            "dag_id",
            "execution_date",
            "dr"."run_id",
            "start_date",
            "end_date",
            "duration",
            "state",
            "try_number",
            "hostname",
            "unixname",
            "job_id",
            "pool",
            "queue",
            "priority_weight",
            "operator",
            "queued_dttm",
            "pid",
            "max_tries"
        FROM
            task_instance ti
        INNER JOIN
            (
                SELECT
                    "execution_date",
                    "run_id"
                FROM
                    dag_run
                GROUP BY
                    run_id,
                    execution_date
            ) dr
        ON
            ti.run_id=dr.run_id
        WHERE
            dag_id LIKE :dag_id
        AND
            execution_date = :execution_date
        ORDER BY
            priority_weight desc,
            start_date
    ''')

    UPDATE_DAG_RUN_STATUS = sqlalchemy.sql.text('''
    UPDATE
        dag_run
    SET
        state = :state
    WHERE
        dag_id = :dag_id
    AND
        execution_date = :execution_date
    ''')

    def __init__(self):
        DbAccess.__init__(self)

    def get_connection_string(self):
        """
        Returns the connection string for this db connection
        """
        return CONF.base.postgresql_airflow_db

    def get_all_dag_runs(self):
        """
        Retrieves all dag runs.
        """
        return self.get_as_dict_array(AirflowDbAccess.SELECT_ALL_DAG_RUNS)

    def get_dag_runs_by_id(self, dag_id, execution_date):
        """
        Retrieves dag runs by dag id and execution date
        """
        return self.get_as_dict_array(
            AirflowDbAccess.SELECT_DAG_RUNS_BY_ID,
            dag_id=dag_id,
            execution_date=execution_date)

    def get_dag_runs_like_id(self, dag_id, execution_date):
        """
        Retrieves dag runs, for parent and child dags by the parent
        dag id and execution date
        """
        return self.get_as_dict_array(
            AirflowDbAccess.SELECT_DAG_RUNS_LIKE_ID,
            dag_id=dag_id + '%',
            execution_date=execution_date)

    def get_all_tasks(self):
        """
        Retrieves all tasks.
        """
        return self.get_as_dict_array(AirflowDbAccess.SELECT_ALL_TASKS)

    def get_tasks_by_id(self, dag_id, execution_date):
        """
        Retrieves tasks by dag id and execution date
        """
        return self.get_as_dict_array(
            AirflowDbAccess.SELECT_TASKS_BY_ID,
            dag_id=dag_id + '%',
            execution_date=execution_date)

    def stop_dag_run(self, dag_id, execution_date):
        """
        Triggers an update to set a dag_run to failed state
        causing dag_run to be stopped
        running -> failed
        """
        self._control_dag_run(
            dag_id=dag_id,
            execution_date=execution_date,
            expected_state='running',
            desired_state='failed')

    def pause_dag_run(self, dag_id, execution_date):
        """
        Triggers an update to set a dag_run to paused state
        causing dag_run to be paused
        running -> paused
        """
        self._control_dag_run(
            dag_id=dag_id,
            execution_date=execution_date,
            expected_state='running',
            desired_state='paused')

    def unpause_dag_run(self, dag_id, execution_date):
        """
        Triggers an update to set a dag_run to running state
        causing dag_run to be unpaused
        paused -> running
        """
        self._control_dag_run(
            dag_id=dag_id,
            execution_date=execution_date,
            expected_state='paused',
            desired_state='running')

    def check_dag_run_state(self, dag_id, execution_date, expected_state):
        """
        Examines a dag_run for state. Throws exception if it's not right
        """
        dag_run_list = self.get_dag_runs_by_id(
            dag_id=dag_id, execution_date=execution_date)
        if dag_run_list:
            dag_run = dag_run_list[0]
            if dag_run['state'] != expected_state:
                raise AirflowStateError(
                    message='dag_run state must be running, but is {}'.format(
                        dag_run['state']))
        else:
            # not found
            raise AirflowStateError(message='dag_run does not exist')

    def _control_dag_run(self, dag_id, execution_date, expected_state,
                         desired_state):
        """
        checks a dag_run's state for expected state, and sets it to the
        desired state
        """
        self.check_dag_run_state(
            dag_id=dag_id,
            execution_date=execution_date,
            expected_state=expected_state)
        self._set_dag_run_state(
            state=desired_state, dag_id=dag_id, execution_date=execution_date)

    def _set_dag_run_state(self, state, dag_id, execution_date):
        """
        Sets a dag run to the specified state.
        WARNING: this assumes that airflow works by reading state from the
        dag_run table dynamically, is not caching results, and doesn't
        start to use the states we're using in a new way.
        """
        self.perform_insert(
            AirflowDbAccess.UPDATE_DAG_RUN_STATUS,
            state=state,
            dag_id=dag_id,
            execution_date=execution_date)
