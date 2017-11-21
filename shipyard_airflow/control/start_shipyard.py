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

from oslo_config import cfg

import shipyard_airflow.control.api as api
from shipyard_airflow import policy
from shipyard_airflow.conf import config
from shipyard_airflow.db import db

CONF = cfg.CONF


def start_shipyard(default_config_files=None):
    """Initializer for shipyard service.

    Sets up global options before setting up API endpoints.
    """
    # Trigger configuration resolution.
    config.parse_args(args=[], default_config_files=default_config_files)

    # Setup root logger
    base_console_handler = logging.StreamHandler()

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[base_console_handler])
    logging.getLogger().info("Setting logging level to: %s",
                             logging.getLevelName(CONF.logging.log_level))

    logging.basicConfig(level=CONF.logging.log_level,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[base_console_handler])

    # Specalized format for API logging
    logger = logging.getLogger('shipyard.control')
    logger.propagate = False
    formatter = logging.Formatter(
        ('%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - '
         '%(external_ctx)s - %(message)s'))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

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
