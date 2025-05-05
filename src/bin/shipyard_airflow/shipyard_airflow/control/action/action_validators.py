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

from shipyard_airflow.control import service_clients
from shipyard_airflow.control.validators.validate_committed_revision import \
    ValidateCommittedRevision
from shipyard_airflow.control.validators.validate_deployment_action import \
    ValidateDeploymentAction
from shipyard_airflow.control.validators.validate_intermediate_commit import \
    ValidateIntermediateCommit
from shipyard_airflow.control.validators.validate_target_nodes import \
    ValidateTargetNodes
from shipyard_airflow.shipyard_const import CustomHeaders

LOG = logging.getLogger(__name__)

addl_headers_map = {
    'context_marker': CustomHeaders.CONTEXT_MARKER.value,
    'user': CustomHeaders.END_USER.value
}


def _get_additional_headers(action):
    """
    Populates additional headers from action dict. The headers sets
    context_marker and end_user for audit trace logging
    :param dict action: action info available
    :returns: dict additional_headers
    """
    addl_headers = {}

    for key, header in addl_headers_map.items():
        header_value = action.get(key)
        if header_value:
            addl_headers.update({header: header_value})

    return addl_headers


def validate_committed_revision(action, **kwargs):
    """Invokes a validation that the committed revision of site design exists
    """
    validator = ValidateCommittedRevision(action=action)
    validator.validate()


def validate_deployment_action_full(action, **kwargs):
    """Validates that the deployment configuration is correctly set up

    Checks:
      - The deployment configuration from Deckhand using the design version
          - If the deployment configuration is missing, error
      - The deployment strategy from the deployment configuration.
          - If the deployment strategy is specified, but is missing, error.
          - Check that there are no cycles in the groups
    """
    addl_headers = _get_additional_headers(action)
    validator = ValidateDeploymentAction(
        dh_client=service_clients.deckhand_client(addl_headers=addl_headers),
        action=action,
        full_validation=True)
    validator.validate()


def validate_deployment_action_basic(action, **kwargs):
    """Validates that the DeploymentConfiguration is present

    Checks:
      - The deployment configuration from Deckhand using the design version
          - If the deployment configuration is missing, error
    """
    addl_headers = _get_additional_headers(action)
    validator = ValidateDeploymentAction(
        dh_client=service_clients.deckhand_client(addl_headers=addl_headers),
        action=action,
        full_validation=False)
    validator.validate()


def validate_intermediate_commits(action, configdocs_helper, **kwargs):
    """Validates that intermediate commits don't exist

    Prevents the execution of an action if there are intermediate commits
    since the last site action. If 'allow_intermediate_commits' is set on the
    action, allows the action to continue
    """
    validator = ValidateIntermediateCommit(action=action,
                                           configdocs_helper=configdocs_helper)
    validator.validate()


def validate_target_nodes(action, **kwargs):
    """Validates the target_nodes parameter

    Ensures the target_nodes is present and properly specified.
    """
    validator = ValidateTargetNodes(action=action)
    validator.validate()
