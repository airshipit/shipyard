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
"""Shipyard startup

Sets up the global configurations for the Shipyard service. Hands off
to the api startup to handle the Falcon specific setup.
"""
from oslo_config import cfg

from shipyard_airflow.conf import config
import shipyard_airflow.control.api as api
from shipyard_airflow.control import ucp_logging
from shipyard_airflow.db import db
from shipyard_airflow import policy

CONF = cfg.CONF


def start_shipyard(default_config_files=None):
    # Trigger configuration resolution.
    config.parse_args(args=[], default_config_files=default_config_files)

    ucp_logging.setup_logging(CONF.logging.log_level)

    # Setup the RBAC policy enforcer
    policy.policy_engine = policy.ShipyardPolicy()
    policy.policy_engine.register_policy()

    # Upgrade database
    if CONF.base.upgrade_db:
        # this is a reasonable place to put any online alembic upgrades
        # desired. Currently only shipyard db is under shipyard control.
        db.SHIPYARD_DB.update_db()

    # Start the API
    return api.start_api()
