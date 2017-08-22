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

from shipyard_airflow import policy
import shipyard_airflow.control.api as api
# We need to import config so the initializing code can run for oslo config
import shipyard_airflow.config as config  # noqa: F401


def start_shipyard():

    # Setup configuration parsing
    cli_options = [
        cfg.BoolOpt(
            'debug', short='d', default=False, help='Enable debug logging'),
    ]

    # Setup root logger
    logger = logging.getLogger('shipyard')

    logger.setLevel('DEBUG')
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Specalized format for API logging
    logger = logging.getLogger('shipyard.control')
    logger.propagate = False
    formatter = logging.Formatter(
        ('%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - '
         '%(external_ctx)s - %(message)s'))

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Setup the RBAC policy enforcer
    policy.policy_engine = policy.ShipyardPolicy()
    policy.policy_engine.register_policy()

    return api.start_api()


# Initialization compatible with PasteDeploy
def paste_start_shipyard(global_conf, **kwargs):
    return shipyard


shipyard = start_shipyard()
