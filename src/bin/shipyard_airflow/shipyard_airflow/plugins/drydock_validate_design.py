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

from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

try:
    from drydock_base_operator import DrydockBaseOperator
except ImportError:
    from shipyard_airflow.plugins.drydock_base_operator import \
        DrydockBaseOperator
from shipyard_airflow.shipyard_const import CustomHeaders

LOG = logging.getLogger(__name__)


class DrydockValidateDesignOperator(DrydockBaseOperator):

    """Drydock Validate Design Operator

    This operator will trigger drydock to validate the
    site design

    """

    def do_execute(self):

        # Form Validation Endpoint
        validation_endpoint = os.path.join(self.drydock_svc_endpoint,
                                           'validatedesign')

        LOG.info("Validation Endpoint is %s", validation_endpoint)

        # Define Headers and Payload
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.svc_token,
            CustomHeaders.CONTEXT_MARKER.value: self.context_marker,
            CustomHeaders.END_USER.value: self.user
        }

        payload = {
            'rel': "design",
            'href': self.design_ref,
            'type': "application/x-yaml"
        }

        # Requests DryDock to validate site design
        LOG.info("Waiting for DryDock to validate site design...")

        try:
            design_validate_response = requests.post(validation_endpoint,
                                                     headers=headers,
                                                     data=json.dumps(payload))

        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        # Convert response to string
        validate_site_design = design_validate_response.text

        # Print response
        LOG.info("Retrieving DryDock validate site design response...")
        LOG.info(json.loads(validate_site_design))

        # Check if site design is valid
        status = str(json.loads(validate_site_design).get('status',
                                                          'unspecified'))
        if status.lower() == 'success':
            LOG.info("DryDock Site Design has been successfully validated")
        else:
            raise AirflowException("DryDock Site Design Validation Failed "
                                   "with status: {}!".format(status))


class DrydockValidateDesignOperatorPlugin(AirflowPlugin):

    """Creates DrydockValidateDesignOperator in Airflow."""

    name = 'drydock_validate_design_operator'
    operators = [DrydockValidateDesignOperator]
