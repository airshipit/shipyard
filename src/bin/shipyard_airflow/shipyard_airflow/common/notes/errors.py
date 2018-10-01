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
"""Errors for the Notes component"""


class NotesError(Exception):
    """Base exception for all NotesErrors"""
    pass


class NotesInitializationError(NotesError):
    """NotesInitializationError

    Raised for errors while initializing a Notes instance
    """
    pass


class NotesRetrievalError(NotesError):
    """NotesRetrievalError

    Raised when there is an error retrieving notes
    """
    pass


class NotesStorageError(NotesError):
    """NotesStorageError

    Raised when there is an error attempting to store a note.
    """
    pass
