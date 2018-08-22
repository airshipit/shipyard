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

from shipyard_airflow.common.deployment_group.deployment_group_manager import (
    DeploymentGroupManager
)
from shipyard_airflow.common.deployment_group.errors import (
    DeploymentGroupCycleError,
    InvalidDeploymentGroupError,
    InvalidDeploymentGroupNodeLookupError
)
from shipyard_airflow.common.deployment_group.node_lookup import NodeLookup
from shipyard_airflow.common.document_validators.document_validator import (
    DocumentValidator
)
from shipyard_airflow.control import service_clients
from shipyard_airflow.control.helpers.design_reference_helper import (
    DesignRefHelper
)
LOG = logging.getLogger(__name__)


def _get_node_lookup(revision_id):
    # get a Drydock node_lookup function using the supplied revision_id

    return NodeLookup(
        service_clients.drydock_client(),
        DesignRefHelper().get_design_reference_href(revision_id)
    ).lookup


def _get_deployment_group_manager(groups, revision_id):
    """Retrieves the deployment group manager"""
    return DeploymentGroupManager(groups, _get_node_lookup(revision_id))


class ValidateDeploymentStrategy(DocumentValidator):
    """Validates the deployment strategy"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    schema = "shipyard/DeploymentStrategy/v1"
    missing_severity = "Error"

    def do_validate(self):
        groups = self.doc_dict['groups']
        try:
            _get_deployment_group_manager(groups, self.revision)
        except DeploymentGroupCycleError as dgce:
            self.val_msg_list.append(self.val_msg(
                name=dgce.__class__.__name__,
                error=True,
                level="Error",
                message=("The deployment groups specified in the Deployment "
                         "Strategy have groups that form a "
                         "cycle."),
                diagnostic=str(dgce)
            ))
            self.error_status = True
        except InvalidDeploymentGroupError as idge:
            self.val_msg_list.append(self.val_msg(
                name=idge.__class__.__name__,
                error=True,
                level="Error",
                message=("A deployment group specified in the Deployment "
                         "Strategy is invalid"),
                diagnostic=str(idge)
            ))
            self.error_status = True
        except InvalidDeploymentGroupNodeLookupError as idgnle:
            self.val_msg_list.append(self.val_msg(
                name=idgnle.__class__.__name__,
                error=True,
                level="Error",
                message=("Shipyard does not have a valid node lookup to "
                         "validate the deployment strategy"),
                diagnostic=str(idgnle)
            ))
            self.error_status = True
        except Exception as ex:
            # all other exceptions are an error
            self.val_msg_list.append(self.val_msg(
                name="DocumentValidationProcessingError",
                error=True,
                level="Error",
                message=("Shipyard has encountered an unexpected error "
                         "while processing document validations"),
                diagnostic=str(ex)
            ))
            self.error_status = True
