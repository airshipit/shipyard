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
"""Action validators module

Validators are run as part of action creation and will raise an ApiError if
there are any validation failures.
"""
import logging

import falcon

from shipyard_airflow.common.document_validators.document_validator_manager \
    import DocumentValidationManager
from shipyard_airflow.control import service_clients
from shipyard_airflow.control.validators.validate_deployment_configuration \
    import ValidateDeploymentConfiguration
from shipyard_airflow.errors import ApiError

LOG = logging.getLogger(__name__)


def validate_site_action(action):
    """Validates that the deployment configuration is correctly set up

    Checks:

      - The deployment configuration from Deckhand using the design version

          - If the deployment configuration is missing, error

      - The deployment strategy from the deployment configuration.

          - If the deployment strategy is specified, but is missing, error.
          - Check that there are no cycles in the groups
    """
    validator = _SiteActionValidator(
        dh_client=service_clients.deckhand_client(),
        action=action
    )
    validator.validate()


class _SiteActionValidator:
    """The validator object setup and used by the validate_site_action function
    """
    def __init__(self, dh_client, action):
        self.action = action
        self.doc_revision = self._get_doc_revision()
        self.cont_on_fail = str(self._action_param(
            'continue-on-fail')).lower() == 'true'
        self.doc_val_mgr = DocumentValidationManager(
            dh_client,
            self.doc_revision,
            [(ValidateDeploymentConfiguration, 'deployment-configuration')]
        )

    def validate(self):
        results = self.doc_val_mgr.validate()
        if self.doc_val_mgr.errored:
            if self.cont_on_fail:
                LOG.warn("Validation failures occured, but 'continue-on-fail' "
                         "is set to true. Processing continues")
            else:
                raise ApiError(
                    title='Document validation failed',
                    description='InvalidConfigurationDocuments',
                    status=falcon.HTTP_400,
                    error_list=results,
                    retry=False,
                )

    def _action_param(self, p_name):
        """Retrieve the value of the specified parameter or None if it doesn't
        exist
        """
        try:
            return self.action['parameters'][p_name]
        except KeyError:
            return None

    def _get_doc_revision(self):
        """Finds the revision id for the committed revision"""
        doc_revision = self.action.get('committed_rev_id')
        if doc_revision is None:
            raise ApiError(
                title='Invalid document revision',
                description='InvalidDocumentRevision',
                status=falcon.HTTP_400,
                error_list=[{
                    'message': (
                        'Action {} with id {} was unable to find a valid '
                        'committed document revision'.format(
                            self.action.get('name'),
                            self.action.get('id')
                        )
                    )
                }],
                retry=False,
            )
        return doc_revision
