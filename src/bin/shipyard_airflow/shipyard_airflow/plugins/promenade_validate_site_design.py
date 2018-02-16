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
import json
import logging
import os
import requests

from airflow.exceptions import AirflowException
from airflow.plugins_manager import AirflowPlugin

try:
    from promenade_base_operator import PromenadeBaseOperator
except ImportError:
    from shipyard_airflow.plugins.promenade_base_operator import (
        PromenadeBaseOperator
    )

LOG = logging.getLogger(__name__)


class PromenadeValidateSiteDesignOperator(PromenadeBaseOperator):
    """
    Promenade Validate Site Design Operator

    This operator will trigger promenade to invoke the validateDesign
    Promenade API
    """

    def do_execute(self):
        LOG.info("Validating site design...")

        # Form Validation Endpoint
        validation_endpoint = os.path.join(self.promenade_svc_endpoint,
                                           'validatedesign')

        LOG.info("Validation Endpoint is %s", validation_endpoint)

        # Define Headers and Payload
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.svc_token
        }

        payload = {
            'rel': "design",
            'href': self.deckhand_design_ref,
            'type': "application/x-yaml"
        }

        # Requests Promenade to validate site design
        LOG.info("Waiting for Promenade to validate site design...")

        try:
            design_validate_response = requests.post(validation_endpoint,
                                                     headers=headers,
                                                     data=json.dumps(payload))

        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        # Convert response to string
        validate_site_design = design_validate_response.text

        # Print response
        LOG.info("Retrieving Promenade validate site design response...")

        try:
            validate_site_design_dict = json.loads(validate_site_design)
            LOG.info(validate_site_design_dict)

        except json.JSONDecodeError as e:
            raise AirflowException(e)

        # Check if site design is valid
        status = validate_site_design_dict.get('status',
                                               'unspecified')

        if status.lower() == 'success':
            LOG.info("Promenade Site Design has been successfully validated")

        else:
            # Dump logs from Promenade pods
            self.get_k8s_logs()

            raise AirflowException("Promenade Site Design Validation Failed "
                                   "with status: {}!".format(status))


class PromenadeValidateSiteDesignOperatorPlugin(AirflowPlugin):

    """Creates PromenadeValidateSiteDesginOperator in Airflow."""

    name = 'promenade_validate_site_design_operator'
    operators = [PromenadeValidateSiteDesignOperator]
