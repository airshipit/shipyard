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
Module to encapsulate thet endpoint lookup for the services used
by Shipyard
"""

import enum
import logging

import falcon
from keystoneauth1 import exceptions as exc
from keystoneauth1 import loading
from oslo_config import cfg

from shipyard_airflow.errors import AppError

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Endpoints(enum.Enum):
    """
    Enumeration of the endpoints that are served by this endpoint manager
    """
    SHIPYARD = 'shipyard'
    DRYDOCK = 'drydock'
    ARMADA = 'armada'
    DECKHAND = 'deckhand'
    PROMENADE = 'promenade'


def _get_service_type(endpoint):
    """
    Because these values should not be used until after initialization,
    they cannot be directly associated with the enum. Thie method takes
    the enum value and retrieves the values when accessed the first time.
    :param Endpoints endpoint: The endpoint to look up
    :returns: The service type value for the named endpoint
    :rtype: str
    :raises AppError: if not provided a valid Endpoints enumeration value
    """
    if isinstance(endpoint, Endpoints):
        endpoint_values = {
            Endpoints.SHIPYARD: CONF.shipyard.service_type,
            Endpoints.DRYDOCK: CONF.drydock.service_type,
            Endpoints.ARMADA: CONF.armada.service_type,
            Endpoints.DECKHAND: CONF.deckhand.service_type,
            Endpoints.PROMENADE: CONF.promenade.service_type
        }
        return endpoint_values.get(endpoint)
    raise AppError(
        title='Endpoint is not known',
        description=(
            'Shipyard is trying to reach an unknown endpoint: {}'.format(
                endpoint.name
            )
        ),
        status=falcon.HTTP_500,
        retry=False
    )


def get_endpoint(endpoint):
    """
    Wraps calls to keystone for lookup of an endpoint by service type
    :param Endpoints endpoint: The endpoint to look up
    :returns: The url string of the endpoint
    :rtype: str
    :raises AppError: if the endpoint cannot be resolved
    """
    service_type = _get_service_type(endpoint)
    try:
        return _get_ks_session().get_endpoint(
            interface='internal',
            service_type=service_type)
    except exc.EndpointNotFound:
        LOG.error('Could not find an internal interface for %s',
                  endpoint.name)
        raise AppError(
            title='Can not access service endpoint',
            description=(
                'Keystone catalog has no internal endpoint for service type: '
                '{}'.format(service_type)
            ),
            status=falcon.HTTP_500,
            retry=False)


def get_token():
    """
    Returns the simple token string for a token acquired from keystone
    """
    return _get_ks_session().get_auth_headers().get('X-Auth-Token')


def get_session():
    """Return the Keystone Session for Shipyard"""
    return _get_ks_session()


def _get_ks_session():
    # Establishes a keystone session
    try:
        return loading.load_session_from_conf_options(
            CONF, group="keystone_authtoken")
    except exc.AuthorizationFailure as aferr:
        LOG.error('Could not authorize against keystone: %s',
                  str(aferr))
        raise AppError(
            title='Could not authorize Shipyard against Keystone',
            description=(
                'Keystone has rejected the authorization request by Shipyard'
            ),
            status=falcon.HTTP_500,
            retry=False
        )
