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
"""Generates clients and client-like objects and functions"""
from urllib.parse import urlparse

from oslo_config import cfg
from deckhand.client import client as dh_client
import drydock_provisioner.drydock_client.client as dd_client
import drydock_provisioner.drydock_client.session as dd_session

from shipyard_airflow.control.service_endpoints import Endpoints
from shipyard_airflow.control import service_endpoints as svc_endpoints

CONF = cfg.CONF


#
# Deckhand Client
#
def deckhand_client():
    """Retrieve a Deckhand client"""
    return dh_client.Client(session=svc_endpoints.get_session(),
                            endpoint_type='internal')


#
# Drydock Client
#
def _auth_gen():
    return [('X-Auth-Token', svc_endpoints.get_token())]


def drydock_client():
    """Retreive a Drydock client"""
    # Setup the drydock session
    endpoint = svc_endpoints.get_endpoint(Endpoints.DRYDOCK)
    dd_url = urlparse(endpoint)
    session = dd_session.DrydockSession(
        dd_url.hostname,
        port=dd_url.port,
        auth_gen=_auth_gen,
        timeout=(CONF.requests_config.drydock_client_connect_timeout,
                 CONF.requests_config.drydock_client_read_timeout))
    return dd_client.DrydockClient(session)
