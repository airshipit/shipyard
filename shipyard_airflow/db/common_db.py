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
module for reused or baseclass portions of DB access
"""

import logging

import sqlalchemy

from shipyard_airflow.errors import DatabaseError

LOG = logging.getLogger(__name__)


class DbAccess:
    """
    Base class for simple database access
    """

    def __init__(self):
        self.engine = None

    def get_connection_string(self):
        """
        Override to return the connection string. This allows for
        lazy initialization
        """
        raise NotImplementedError()

    def update_db(self):
        """
        Unimplemented method for use in overriding to peform db updates
        """
        LOG.info('No databse version updates specified for %s',
                 self.__class__.__name__)

    def get_engine(self):
        """
        Returns the engine for airflow
        """
        try:
            connection_string = self.get_connection_string()
            if connection_string is not None and self.engine is None:
                self.engine = sqlalchemy.create_engine(connection_string)
            if self.engine is None:
                self._raise_invalid_db_config(
                    connection_string=connection_string
                )
            LOG.info('Connected with <%s>, returning engine',
                     connection_string)
            return self.engine
        except sqlalchemy.exc.ArgumentError as exc:
            self._raise_invalid_db_config(
                exception=exc,
                connection_string=connection_string
            )

    def _raise_invalid_db_config(self,
                                 connection_string,
                                 exception=None):
        """
        Common handler for an invalid DB connection
        """
        LOG.error('Connection string <%s> prevents database operation',
                  connection_string)
        if exception is not None:
            LOG.error("Associated exception: %s", exception)
        raise DatabaseError(
            title='No database connection',
            description='Invalid database configuration'
        )

    def get_as_dict_array(self, query, **kwargs):
        """
        executes the supplied query and returns the array of dictionaries of
        the row results
        """
        LOG.info('Query: %s', query)
        result_dict_list = []
        if query is not None:
            with self.get_engine().connect() as connection:
                result_set = connection.execute(query, **kwargs)
                result_dict_list = [dict(row) for row in result_set]
        LOG.info('Result has %s rows', len(result_dict_list))
        for dict_row in result_dict_list:
            LOG.info('Result: %s', dict_row)
        return result_dict_list

    def perform_insert(self, query, **kwargs):
        """
        Performs a parameterized insert
        """
        return self.perform_change_dml(query, **kwargs)

    def perform_update(self, query, **kwargs):
        """
        Performs a parameterized update
        """
        return self.perform_change_dml(query, **kwargs)

    def perform_delete(self, query, **kwargs):
        """
        Performs a parameterized delete
        """
        return self.perform_change_dml(query, **kwargs)

    def perform_change_dml(self, query, **kwargs):
        """
        Performs an update/insert/delete
        """
        LOG.debug('Query: %s', query)
        if query is not None:
            with self.get_engine().connect() as connection:
                return connection.execute(query, **kwargs)
