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
"""Classes and functions to support Shipyard specific document validation

Only validates that which is not already covered by schema validation, which
is performed by Deckhand on Shipyard's behalf.
"""
import logging

from shipyard_airflow.common.document_validators.document_validator import (
    DocumentValidator
)
from .validate_deployment_strategy import ValidateDeploymentStrategy

LOG = logging.getLogger(__name__)


class ValidateDeploymentConfiguration(DocumentValidator):
    """Validates the DeploymentConfiguration."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "shipyard/DeploymentConfiguration/v1"
    missing_severity = "Error"

    def do_validate(self):
        try:
            dep_strat_nm = (
                self.doc_dict['physical_provisioner']['deployment_strategy']
            )
            self.add_triggered_validation(ValidateDeploymentStrategy,
                                          dep_strat_nm)

        except KeyError:
            self.val_msg_list.append(self.val_msg(
                name="DeploymentStrategyNotSpecified",
                error=False,
                level="Info",
                message=("A deployment strategy document was not specified in "
                         "the deployment configuration. Because of this, the "
                         "strategy used will be all-at-once.")
            ))
            LOG.info("No deployment strategy document specified, "
                     "'all-at-once' is assumed, and deployment strategy will "
                     "not be further validated")

        self.error_status = False
