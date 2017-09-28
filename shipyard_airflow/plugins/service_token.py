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

from functools import wraps

from keystoneauth1.identity import v3 as keystone_v3
from keystoneauth1 import session as keystone_session
from keystoneclient.v3 import client as keystone_client


def shipyard_service_token(func):
    @wraps(func)
    def keystone_token_get(self, context):
        # Read and parse shiyard.conf
        config = configparser.ConfigParser()
        config.read(self.shipyard_conf)

        # Initialize variables
        retry = 0
        token = None
        keystone_auth = {}

        # We will allow 1 retry in getting the Keystone Token with a
        # backoff interval of 10 seconds in case there is a temporary
        # glitch in the network or transient problems with the keystone-api
        # pod
        while retry <= 1:
            # Construct Session Argument
            for attr in ('auth_url', 'password', 'project_domain_name',
                         'project_name', 'username', 'user_domain_name'):
                keystone_auth[attr] = config.get('keystone_authtoken', attr)

            # Set up keystone session
            auth = keystone_v3.Password(**keystone_auth)
            sess = keystone_session.Session(auth=auth)
            keystone = keystone_client.Client(session=sess)

            # Retrieve Keystone Token
            logging.info("Get Keystone Token")
            token = keystone.get_raw_token_from_identity_service(
                **keystone_auth)['auth_token']

            # Retry if we fail to get the keystone token
            if token:
                logging.info("Successfully Retrieved Keystone Token")
                context['svc_token'] = token
                break
            else:
                logging.info("Unable to get Keystone Token on first attempt")
                logging.info("Retrying after 10 seconds...")
                time.sleep(10)
                retry += 1

        # Raise Execptions if we fail to get a proper response
        if not token:
            raise AirflowException("Unable to get Keystone Token!")
        else:
            return func(self, context)

    return keystone_token_get
