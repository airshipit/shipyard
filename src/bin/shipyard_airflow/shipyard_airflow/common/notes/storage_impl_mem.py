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
"""Implementations of the NotesStorage base class"""
from .errors import NoteNotFoundError
from .notes import NotesStorage


class MemoryNotesStorage(NotesStorage):
    """In-memory note storage

    Primarily useful for testing
    """

    def __init__(self):
        self.storage = {}

    def store(self, note):
        self.storage[note.note_id] = note
        return note

    def retrieve(self, query):
        pat = query.assoc_id_pattern
        max_verb = query.max_verbosity
        notes = []
        if query.exact_match:
            for note in self.storage.values():
                if note.assoc_id == pat and note.verbosity <= max_verb:
                    notes.append(note)
        else:
            for note in self.storage.values():
                if (note.assoc_id.startswith(pat) and
                        note.verbosity <= max_verb):
                    notes.append(note)
        notes.sort(key=lambda x: x.note_timestamp)
        return notes

    def retrieve_by_id(self, note_id):
        note = self.storage.get(note_id)
        if not note:
            raise NoteNotFoundError()
        return note
