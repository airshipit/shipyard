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

from functools import wraps
import logging
import time

from airflow.exceptions import AirflowException

from service_session import ucp_keystone_session


def shipyard_service_token(func):
    @wraps(func)
    def keystone_token_get(self, *args):
        """This function retrieves Keystone token for UCP Services

        :param context: Information on the current workflow

        Example::

            from service_token import shipyard_service_token

            @shipyard_service_token
            def on_get(self, svc_endpoint):
                logging.info("The token is %s", self.svc_token)

                # Use the token to perform tasks such as setting
                # up a DrydockSession which requires keystone
                # token for authentication
        """
        # Initialize variables
        retry = 0

        # Retrieve Keystone Session
        self.svc_session = ucp_keystone_session(self)

        # We will allow 1 retry in getting the Keystone Token with a
        # backoff interval of 10 seconds in case there is a temporary
        # glitch in the network or transient problems with the keystone-api
        # pod
        while retry <= 1:
            # Retrieve Keystone Token
            logging.info("Get Keystone Token")
            self.svc_token = self.svc_session.get_auth_headers().get(
                'X-Auth-Token')

            # Retry if we fail to get the keystone token
            if self.svc_token:
                logging.info("Successfully Retrieved Keystone Token")
                break
            else:
                logging.info("Unable to get Keystone Token on first attempt")
                logging.info("Retrying after 10 seconds...")
                time.sleep(10)
                retry += 1

        # Raise Execptions if we fail to get a proper response
        if not self.svc_token:
            raise AirflowException("Unable to get Keystone Token!")
        else:
            return func(self, *args)

    return keystone_token_get
