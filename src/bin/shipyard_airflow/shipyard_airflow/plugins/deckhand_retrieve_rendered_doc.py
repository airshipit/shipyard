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

from airflow.plugins_manager import AirflowPlugin
from airflow.exceptions import AirflowException

try:
    from deckhand_base_operator import DeckhandBaseOperator
except ImportError:
    from shipyard_airflow.plugins.deckhand_base_operator import \
        DeckhandBaseOperator


LOG = logging.getLogger(__name__)


class DeckhandRetrieveRenderedDocOperator(DeckhandBaseOperator):

    """Deckhand Retrieve Rendered Doc Operator

    This operator will trigger deckhand to retrieve rendered doc

    """

    def do_execute(self):

        LOG.info("Retrieving Rendered Document...")

        # Retrieve Rendered Document
        try:
            self.deckhandclient.revisions.documents(
                self.revision_id, rendered=True)

            LOG.info("Successfully Retrieved Rendered Document")

        except:
            # Dump logs from Deckhand pods
            self.get_k8s_logs()

            raise AirflowException("Failed to Retrieve Rendered Document!")


class DeckhandRetrieveRenderedDocOperatorPlugin(AirflowPlugin):

    """Creates DeckhandRetrieveRenderedDocOperator in Airflow."""

    name = 'deckhand_retrieve_rendered_doc_operator'
    operators = [DeckhandRetrieveRenderedDocOperator]
