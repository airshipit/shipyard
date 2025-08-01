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

Set up a validator for the DeploymentData document generated by pegleg
Only validates that which is not already covered by schema validation, which
is performed by Deckhand on Shipyard's behalf.
"""
from shipyard_airflow.common.document_validators.document_validator import (
    DocumentValidator)
import logging
from oslo_config import cfg

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ValidateDeploymentVersion(DocumentValidator):
    """Validates the existence of the deployment data document"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = CONF.document_info.deployment_version_schema
    # Just capitalize the "missing_severity", and then the base class will take
    # care of whether or not the value is actually valid
    missing_severity = CONF.validations.deployment_version_commit.capitalize()

    def do_validate(self):
        # Need to define this since it is abstract in the base class, but all
        # we need to check for this document is its existence, which is taken
        # care of by the validate() function in the base class
        pass
