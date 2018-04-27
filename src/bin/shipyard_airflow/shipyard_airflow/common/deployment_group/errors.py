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
#


class InvalidDeploymentGroupError(Exception):
    """InvalidDeploymentGroupError

    Represents that a deployment group's configuration is invalid
    """
    pass


class InvalidDeploymentGroupNodeLookupError(Exception):
    """InvalidDeploymentGroupNodeLookupError

    Indicates that there is a problem with the node lookup function
    provided to the deployment group
    """
    pass


class DeploymentGroupLabelFormatError(Exception):
    """DeploymentGroupLabelFormatError

    Indicates that a value that is intended to be a label is not formatted
    correctly
    """
    pass


class DeploymentGroupCycleError(Exception):
    """DeploymentGroupCycleError

    Raised when a set of deployment groups have a dependency cycle
    """
    pass


class DeploymentGroupStageError(Exception):
    """DeploymentGroupStageError

    Raised for invalid operations while processing stages
    """
    pass


class UnknownDeploymentGroupError(Exception):
    """UnknownDeploymentGroupError

    Raised when there is an attempt to access a deployment group that isn't
    recognized by the system
    """
    pass


class UnknownNodeError(Exception):
    """UnknownNodeError

    Raised when trying to access a node that does not exist
    """
    pass
