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
import time

from airflow.exceptions import AirflowException

from service_session import ucp_keystone_session


def ucp_service_endpoint(self, context):

    # Initialize variables
    retry = 0
    int_endpoint = None

    # Retrieve Keystone Session
    sess = ucp_keystone_session(self, context)

    # We will allow 1 retry in getting the Keystone Endpoint with a
    # backoff interval of 10 seconds in case there is a temporary
    # glitch in the network or transient problems with the keystone-api
    # pod
    while retry <= 1:
        # Retrieve Keystone Endpoint
        # We will make use of internal endpoint
        logging.info("Get Keystone Endpoint")
        int_endpoint = sess.get_endpoint(interface='internal',
                                         service_type=context['svc_type'])

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
