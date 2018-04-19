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

from deckhand_base_operator import DeckhandBaseOperator

LOG = logging.getLogger(__name__)


class DeckhandGetDesignOperator(DeckhandBaseOperator):

    """Deckhand Get Design Operator

    This operator will trigger deckhand to retrieve the last
    committed revision and save it in airflow as xcom

    """

    def do_execute(self):

        # Retrieve Keystone Token and assign to X-Auth-Token Header
        x_auth_token = {"X-Auth-Token": self.svc_token}

        # Form Revision Endpoint
        revision_endpoint = os.path.join(self.deckhand_svc_endpoint,
                                         'revisions')

        # Retrieve Revision
        LOG.info("Retrieving revisions information...")

        try:
            query_params = {'tag': 'committed', 'sort': 'id', 'order': 'desc'}
            revisions = yaml.safe_load(requests.get(
                revision_endpoint,
                headers=x_auth_token,
                params=query_params,
                timeout=self.deckhand_client_read_timeout).text)

        except requests.exceptions.RequestException as e:
            # Dump logs from Deckhand pods
            self.get_k8s_logs()

            raise AirflowException(e)

        # Print info about revisions from DeckHand
        LOG.info("Revisions response: %s", revisions)
        LOG.info("The number of committed revisions is %s",
                 revisions['count'])

        # Search for the latest committed version and save it as xcom.
        # Since the order : desc paramater above, this is index 0 if there
        # are any results
        revision_list = revisions.get('results', [])
        if revision_list:
            self.committed_ver = revision_list[0].get('id')
            LOG.info("Latest committed revision is %d", self.committed_ver)

        # Error if we cannot resolve the committed version to use.
        if not self.committed_ver:
            # Dump logs from Deckhand pods
            self.get_k8s_logs()

            raise AirflowException("No committed revision found in Deckhand!")


class DeckhandGetDesignOperatorPlugin(AirflowPlugin):

    """Creates DeckhandGetDesignOperator in Airflow."""

    name = 'deckhand_get_design_operator'
    operators = [DeckhandGetDesignOperator]
