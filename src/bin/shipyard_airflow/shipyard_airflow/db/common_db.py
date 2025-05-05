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

from oslo_config import cfg
import sqlalchemy

from shipyard_airflow.errors import DatabaseError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class DbAccess:
    """
    Base class for simple database access
    """

    def __init__(self):
        self.engine = None
        # Descendent classes can override these after construciton, but before
        # invoking get_engine, if there is a need to tailor the values
        # for that specific database.
        self.pool_size = CONF.base.pool_size
        self.max_overflow = CONF.base.pool_overflow
        self.pool_pre_ping = CONF.base.pool_pre_ping
        self.pool_recycle = CONF.base.connection_recycle
        self.pool_timeout = CONF.base.pool_timeout

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
        LOG.info('No database version updates specified for %s',
                 self.__class__.__name__)

    def get_engine(self):
        """
        Returns the engine for airflow
        """
        try:
            connection_string = self.get_connection_string()
            if connection_string is not None and self.engine is None:
                LOG.info(
                    'Initializing connection <%s> with pool size: %d, '
                    'max overflow: %d, pool pre ping: %s, pool '
                    'recycle: %d, and pool timeout: %d', connection_string,
                    self.pool_size, self.max_overflow, self.pool_pre_ping,
                    self.pool_recycle, self.pool_timeout)
                self.engine = sqlalchemy.create_engine(
                    connection_string,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_pre_ping=self.pool_pre_ping,
                    pool_recycle=self.pool_recycle,
                    pool_timeout=self.pool_timeout)
            if self.engine is None:
                self._raise_invalid_db_config(
                    connection_string=connection_string)
            LOG.info('Connected with <%s>, returning engine',
                     connection_string)
            return self.engine
        except sqlalchemy.exc.ArgumentError as exc:
            self._raise_invalid_db_config(exception=exc,
                                          connection_string=connection_string)

    def _raise_invalid_db_config(self, connection_string, exception=None):
        """
        Common handler for an invalid DB connection
        """
        LOG.error('Connection string <%s> prevents database operation',
                  connection_string)
        if exception is not None:
            LOG.error("Associated exception: %s", exception)
        raise DatabaseError(title='No database connection',
                            description='Invalid database configuration')

    def get_as_dict_array(self, query, **kwargs):
        """
        executes the supplied query and returns the array of dictionaries of
        the row results
        """
        LOG.debug('Query: %s', _query_single_line(query))
        result_dict_list = []
        if query is not None:
            with self.get_engine().connect() as connection:
                result_set = connection.execute(query, **kwargs)
                result_dict_list = [dict(row) for row in result_set]
        LOG.info('Result has %s rows', len(result_dict_list))
        for dict_row in result_dict_list:
            LOG.debug('Result: %s', dict_row)
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
        LOG.debug('Query: %s', _query_single_line(query))
        if query is not None:
            with self.get_engine().connect() as connection:
                return connection.execute(query, **kwargs)


def _query_single_line(query):
    """Reformats a query string to remove newlines and extra spaces

    :param query: The query to log. This will work for anything that will
        result in a string after str() is applied to it. Be aware of this
        conversion. E.g. sqlalchemy's TextClause objects.
    """
    return " ".join(str(query).split())
