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
    def keystone_token_get(self, context, *args):
        """This function retrieves Keystone token for UCP Services

        :param context: Information on the current workflow

        Example::

            from service_token import shipyard_service_token

            @shipyard_service_token
            def on_get(self, context):
                svc_token=context['svc_token']

                # Use the token to perform tasks such as setting
                # up a DrydockSession which requires keystone
                # token for authentication
        """
        # Initialize variables
        retry = 0
        token = None

        # Retrieve Keystone Session
        sess = ucp_keystone_session(self, context)

        # We will allow 1 retry in getting the Keystone Token with a
        # backoff interval of 10 seconds in case there is a temporary
        # glitch in the network or transient problems with the keystone-api
        # pod
        while retry <= 1:
            # Retrieve Keystone Token
            logging.info("Get Keystone Token")
            token = sess.get_auth_headers().get('X-Auth-Token')

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
            return func(self, context, *args)

    return keystone_token_get
