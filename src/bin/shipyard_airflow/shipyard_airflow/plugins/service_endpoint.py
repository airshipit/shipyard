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
import configparser
import logging
import time

from airflow.exceptions import AirflowException

try:
    from service_session import ucp_keystone_session
except ImportError:
    from shipyard_airflow.plugins.service_session import ucp_keystone_session

# Lookup values for configuration to find the real service type for components
SHIPYARD = 'shipyard'
DRYDOCK = 'drydock'
ARMADA = 'armada'
DECKHAND = 'deckhand'
PROMENADE = 'promenade'

LOG = logging.getLogger(__name__)


def _ucp_service_endpoint(shipyard_conf, svc_type, addl_headers=None):

    # Initialize variables
    retry = 0
    int_endpoint = None

    # Retrieve Keystone Session
    sess = ucp_keystone_session(shipyard_conf,
                                additional_headers=addl_headers)

    # We will allow 1 retry in getting the Keystone Endpoint with a
    # backoff interval of 10 seconds in case there is a temporary
    # glitch in the network or transient problems with the keystone-api
    # pod
    while retry <= 1:
        # Retrieve Keystone Endpoint
        # We will make use of internal endpoint
        logging.info("Get Keystone Endpoint")
        int_endpoint = sess.get_endpoint(interface='internal',
                                         service_type=svc_type)

        # Retry if we fail to get keystone endpoint
        if int_endpoint:
            logging.info("Successfully Retrieved Keystone Endpoint")
            break
        else:
            logging.info("Unable to get Keystone endpoint on first attempt")
            logging.info("Retrying after 10 seconds...")
            time.sleep(10)
            retry += 1

    # Raise Execptions if we fail to get the keystone endpoint
    if not int_endpoint:
        raise AirflowException("Unable to get Keystone Endpoint!")
    else:
        return int_endpoint


class ServiceEndpoints():
    """Class that serves service endpoints"""
    def __init__(self, shipyard_conf):
        self.shipyard_conf = shipyard_conf

        # Read and parse shiyard.conf
        self.config = configparser.ConfigParser()
        self.config.read(self.shipyard_conf)

    def endpoint_by_name(self, svc_name, addl_headers=None):
        """Return the service endpoint for the named service.

        :param svc_name: name of the service from which the service type will
            be discovered from the shipyard configuration. Constants in this
            module provide names that can be used with an expectation that they
            work with a standard/complete configuration file.
            E.g.: service_endpoint.DRYDOCK
        :param dict addl_headers: Additional headers that should be attached
            to every request passing through the session.
            Headers of the same name specified per request will take priority.
        """
        LOG.info("Looking up service endpoint for: %s", svc_name)
        svc_type = self.config.get(svc_name, 'service_type')
        return _ucp_service_endpoint(self.shipyard_conf,
                                     svc_type,
                                     addl_headers=addl_headers)
