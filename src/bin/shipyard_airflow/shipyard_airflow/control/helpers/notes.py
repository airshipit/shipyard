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
#
"""Notes

Provides setup and access to a NotesHelper object that is used across the
API
"""
import logging

from oslo_config import cfg

from shipyard_airflow.common.notes.notes import NotesManager
from shipyard_airflow.common.notes.notes_helper import NotesHelper
from shipyard_airflow.common.notes.storage_impl_db import (
    ShipyardSQLNotesStorage
)
from shipyard_airflow.control.service_endpoints import get_token
from shipyard_airflow.db.db import SHIPYARD_DB

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def _notes_manager():
    """Setup a NotesManager object using Shipyard settings"""
    sy_engine_getter = SHIPYARD_DB.get_engine
    return NotesManager(
        ShipyardSQLNotesStorage(sy_engine_getter),
        get_token,
        CONF.requests_config.notes_connect_timeout,
        CONF.requests_config.notes_read_timeout
    )


# NOTES is the notes manager that can be imported and used by other modules
# for notes functionality across the Shipyard API.
NOTES = NotesHelper(_notes_manager())
