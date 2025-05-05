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
import logging

from oslo_config import cfg
from werkzeug.middleware.profiler import ProfilerMiddleware

from shipyard_airflow.conf import config
import shipyard_airflow.control.api as api
from shipyard_airflow.control.logging.logging_config import LoggingConfig
from shipyard_airflow import policy

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def start_shipyard(default_config_files=None):
    # Trigger configuration resolution.
    config.parse_args(args=[], default_config_files=default_config_files)

    LoggingConfig(level=CONF.logging.log_level,
                  named_levels=CONF.logging.named_log_levels).setup_logging()

    # Setup the RBAC policy enforcer
    policy.policy_engine = policy.ShipyardPolicy()
    policy.policy_engine.register_policy()

    # Start the API
    if CONF.base.profiler:
        LOG.warning("Profiler ENABLED. Expect significant "
                    "performance overhead.")
        return ProfilerMiddleware(api.start_api(),
                                  profile_dir="/tmp/profiles")  # nosec
    else:
        return api.start_api()
