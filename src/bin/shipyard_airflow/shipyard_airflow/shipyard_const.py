# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
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
"""Constants definition module for Shipyard.

"""
import enum


class CustomHeaders(enum.Enum):
    """
    Enumerations of Custom HTTP Headers key.
    """
    END_USER = 'X-End-User'
    CONTEXT_MARKER = 'X-Context-Marker'

# TODO: Other constants that are used across modules in Shipyard
# to be defined here for better maintainability
