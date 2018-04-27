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
"""Errors raised by the document validators"""


class DeckhandClientRequiredError(Exception):
    """Signals that a Deckhand client was required but was not provided"""


class DocumentLookupError(Exception):
    """Signals that an error occurred while looking up a document"""
    pass


class DocumentNotFoundError(Exception):
    """Signals that a document that was expected to be found was not found"""
    pass
