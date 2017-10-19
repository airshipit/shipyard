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
Shipyard database access - see db.py for instances to use
"""
import json
import logging
import os

import sqlalchemy
from alembic import command as alembic_command
from alembic.config import Config
from oslo_config import cfg

from shipyard_airflow.db.common_db import DbAccess

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ShipyardDbAccess(DbAccess):
    """
    Shipyard database access
    """

    SELECT_ALL_ACTIONS = sqlalchemy.sql.text('''
    SELECT
        "id",
        "name",
        "parameters",
        "dag_id",
        "dag_execution_date",
        "user",
        "datetime",
        "context_marker"
    FROM
        actions
    ''')

    SELECT_ACTION_BY_ID = sqlalchemy.sql.text('''
    SELECT
        "id",
        "name",
        "parameters",
        "dag_id",
        "dag_execution_date",
        "user",
        "datetime",
        "context_marker"
    FROM
        actions
    WHERE
        id = :action_id
    ''')

    INSERT_ACTION = sqlalchemy.sql.text('''
    INSERT INTO
        actions (
            "id",
            "name",
            "parameters",
            "dag_id",
            "dag_execution_date",
            "user",
            "datetime",
            "context_marker"
        )
    VALUES (
        :id,
        :name,
        :parameters,
        :dag_id,
        :dag_execution_date,
        :user,
        :timestamp,
        :context_marker )
    ''')

    SELECT_VALIDATIONS = sqlalchemy.sql.text('''
    SELECT
        "id",
        "action_id",
        "validation_name"
    FROM
        preflight_validation_failures
    ''')

    SELECT_VALIDATION_BY_ID = sqlalchemy.sql.text('''
    SELECT
        "id",
        "action_id",
        "validation_name",
        "details"
    FROM
        preflight_validation_failures
    WHERE
        id = :validation_id
    ''')

    SELECT_VALIDATION_BY_ACTION_ID = sqlalchemy.sql.text('''
    SELECT
        "id",
        "action_id",
        "validation_name",
        "details"
    FROM
        preflight_validation_failures
    WHERE
        action_id = :action_id
    ''')

    SELECT_CMD_AUDIT_BY_ACTION_ID = sqlalchemy.sql.text('''
    SELECT
        "id",
        "action_id",
        "command",
        "user",
        "datetime"
    FROM
        action_command_audit
    WHERE
        action_id = :action_id
    ''')

    INSERT_ACTION_COMMAND_AUDIT = sqlalchemy.sql.text('''
    INSERT INTO
        action_command_audit (
            "id",
            "action_id",
            "command",
            "user"
        )
    VALUES (
        :id,
        :action_id,
        :command,
        :user )
    ''')

    # Insert a lock record if there's not a conflicting one
    INSERT_API_LOCK = sqlalchemy.sql.text('''
    INSERT INTO
        api_locks (
            "id",
            "lock_type",
            "datetime",
            "expires",
            "released",
            "user",
            "reference_id"
        )
    SELECT
        :id,
        :lock_type,
        CURRENT_TIMESTAMP,
        :expires,
        'false',
        :user,
        :reference_id
    WHERE
        NOT EXISTS (SELECT
            "id"
        FROM
            api_locks
        WHERE
            "lock_type" = :lock_type
            AND "released" = 'false'
            AND "datetime" + (interval '1 second' * "expires") > now())
    ''')

    # Find the latest active lock for the type
    SELECT_LATEST_LOCK_BY_TYPE = sqlalchemy.sql.text('''
    SELECT
        "id"
    FROM
        api_locks
    WHERE
        "lock_type" = :lock_type
        AND "datetime" + (interval '1 second' * "expires") > now()
        AND "released" = 'false'
    ORDER BY
        "datetime" DESC,
        "id" DESC
    LIMIT 1
    ''')

    # Releasea a lock
    UPDATE_LOCK_RELEASE = sqlalchemy.sql.text('''
    UPDATE
        api_locks
    SET
        "released" = 'true'
    WHERE
        "id" = :id
    ''')

    def __init__(self):
        DbAccess.__init__(self)

    def get_connection_string(self):
        """
        Returns the connection string for this db connection
        """

        return CONF.base.postgresql_db

    def update_db(self):
        """
        Trigger Alembic to upgrade to the latest version of the DB
        """
        try:
            LOG.info("Checking for shipyard database upgrade")
            cwd = os.getcwd()
            os.chdir(CONF.base.alembic_ini_path)
            config = Config('alembic.ini',
                            attributes={'configure_logger': False})
            alembic_command.upgrade(config, 'head')
            os.chdir(cwd)
        except Exception as exception:
            LOG.error('***\n'
                      'Failed Alembic DB upgrade. Check the config: %s\n'
                      '***',
                      exception)
            # don't let things continue...
            raise exception

    def get_all_submitted_actions(self):
        """
        Retrieves all actions.
        """
        return self.get_as_dict_array(ShipyardDbAccess.SELECT_ALL_ACTIONS)

    def get_action_by_id(self, action_id):
        """
        Get a single action
        :param action_id: the id of the action to retrieve
        """
        actions_array = self.get_as_dict_array(
            ShipyardDbAccess.SELECT_ACTION_BY_ID, action_id=action_id)
        if actions_array:
            return actions_array[0]
        # Not found
        return None

    def get_preflight_validation_fails(self):
        """
        Retrieves the summary set of preflight validation failures
        """
        return self.get_as_dict_array(ShipyardDbAccess.SELECT_VALIDATIONS)

    def get_validation_by_id(self, validation_id):
        """
        Retreives a single validation for a given validation id
        """
        validation_array = self.get_as_dict_array(
            ShipyardDbAccess.SELECT_VALIDATION_BY_ID,
            validation_id=validation_id)
        if validation_array:
            return validation_array[0]
        # No validations
        return None

    def get_validation_by_action_id(self, action_id):
        """
        Retreives the validations for a given action id
        """
        return self.get_as_dict_array(
            ShipyardDbAccess.SELECT_VALIDATION_BY_ACTION_ID,
            action_id=action_id)

    def insert_action(self, action):
        """
        Inserts a single action row
        """
        self.perform_insert(ShipyardDbAccess.INSERT_ACTION,
                            id=action['id'],
                            name=action['name'],
                            parameters=json.dumps(action['parameters']),
                            dag_id=action['dag_id'],
                            dag_execution_date=action['dag_execution_date'],
                            user=action['user'],
                            timestamp=action['timestamp'],
                            context_marker=action['context_marker'])

    def get_command_audit_by_action_id(self, action_id):
        """
        Retreives the action audit records for a given action id
        """
        return self.get_as_dict_array(
            ShipyardDbAccess.SELECT_CMD_AUDIT_BY_ACTION_ID,
            action_id=action_id)

    def insert_action_command_audit(self, ac_audit):
        """
        Inserts a single action command audit
        """
        self.perform_insert(ShipyardDbAccess.INSERT_ACTION_COMMAND_AUDIT,
                            id=ac_audit['id'],
                            action_id=ac_audit['action_id'],
                            command=ac_audit['command'],
                            user=ac_audit['user'])

    def insert_api_lock(self,
                        lock_id,
                        lock_type,
                        expires,
                        user,
                        reference_id):
        """
        Inserts an api lock
        """
        result = self.perform_insert(ShipyardDbAccess.INSERT_API_LOCK,
                                     id=lock_id,
                                     lock_type=lock_type,
                                     expires=expires,
                                     user=user,
                                     reference_id=reference_id)
        return result.rowcount == 1

    def get_api_lock(self, lock_type):
        """
        Retreives the id of the newest current lock for the given
        type.
        """
        result_dict = self.get_as_dict_array(
            ShipyardDbAccess.SELECT_LATEST_LOCK_BY_TYPE,
            lock_type=lock_type
        )
        if result_dict:
            return result_dict[0].get('id')
        # No lock found
        return None

    def release_api_lock(self, lock_id):
        """
        Marks the lock specified by the id as released.
        """
        self.perform_update(ShipyardDbAccess.UPDATE_LOCK_RELEASE,
                            id=lock_id)
