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
import logging
import os
import requests
import yaml

from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

try:
    from deckhand_base_operator import DeckhandBaseOperator
except ImportError:
    from shipyard_airflow.plugins.deckhand_base_operator import \
        DeckhandBaseOperator

LOG = logging.getLogger(__name__)


class DeckhandValidateSiteDesignOperator(DeckhandBaseOperator):

    """Deckhand Validate Site Design Operator

    This operator will trigger deckhand to validate the
    site design YAMLs

    """

    def do_execute(self):

        # Retrieve Keystone Token and assign to X-Auth-Token Header
        x_auth_token = {"X-Auth-Token": self.svc_token}

        # Form Validation Endpoint
        validation_endpoint = os.path.join(self.deckhand_svc_endpoint,
                                           'revisions',
                                           str(self.revision_id),
                                           'validations')
        # Retrieve Validation list
        LOG.info("Retrieving validation list...")

        try:
            retrieved_list = yaml.safe_load(
                requests.get(validation_endpoint,
                             headers=x_auth_token,
                             timeout=(self.validation_connect_timeout,
                                      self.validation_read_timeout)).text)

        except requests.exceptions.RequestException as e:
            raise AirflowException(e)

        if (any([str(v.get('status', 'unspecified')).lower() == 'failure'
                for v in retrieved_list.get('results', [])])):
            raise AirflowException("DeckHand Site Design Validation Failed!")
        else:
            LOG.info("Revision %d has been successfully validated",
                     self.revision_id)


class DeckhandValidateSiteDesignOperatorPlugin(AirflowPlugin):

    """Creates DeckhandValidateSiteDesignOperator in Airflow."""

    name = 'deckhand_validate_site_design_operator'
    operators = [DeckhandValidateSiteDesignOperator]
