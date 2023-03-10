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

import falcon
from oslo_config import cfg

from .validate_deployment_configuration \
    import ValidateDeploymentConfigurationBasic
from .validate_deployment_configuration \
    import ValidateDeploymentConfigurationFull
from shipyard_airflow.common.document_validators.document_validator_manager \
    import DocumentValidationManager
from shipyard_airflow.errors import ApiError

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ValidateDeploymentAction:
    """The validator used by the validate_deployment_action_<x> functions
    """
    def __init__(self, dh_client, action, full_validation=True):
        self.action = action
        self.doc_revision = self.action.get('committed_rev_id')
        self.cont_on_fail = str(self._action_param(
            'continue-on-fail')).lower() == 'true'
        if full_validation:
            # Perform a complete validation
            self.doc_val_mgr = DocumentValidationManager(
                dh_client,
                self.doc_revision,
                [(ValidateDeploymentConfigurationFull,
                  CONF.document_info.deployment_configuration_name)]
            )
        else:
            # Perform a basic validation only
            self.doc_val_mgr = DocumentValidationManager(
                dh_client,
                self.doc_revision,
                [(ValidateDeploymentConfigurationBasic,
                  CONF.document_info.deployment_configuration_name)]
            )

    def validate(self):
        results = self.doc_val_mgr.validate()
        if self.doc_val_mgr.errored:
            if self.cont_on_fail:
                LOG.warning("Validation failures occured, "
                            "but 'continue-on-fail' "
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
