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
from enum import Enum
import logging

from .notes import MAX_VERBOSITY
from .notes import MIN_VERBOSITY
from .notes import Query

LOG = logging.getLogger(__name__)


class _NoteType:
    """Define the patterns and pertinent positions of information for a note

    :param root: the string used as the initial identifier for the type
    :param key_pattern_count: the number of variable positions in the key.
        E.g.: a value of 3, and a root of "tacos" would generate a key_pattern
        of "tacos/{}/{}/{}", while a value of 0 would generate "tacos".
        The lookup_pattern for a type is also drived from the key_pattern_count
        by subtracting 1 (minimum 0), such that a value of 3 and a root of
        "tacos" would generate a lookup_pattern of "tacos/{}/{}/
    :param id_start: the start location in the assoc_id of a note of this type
        where the id of the item it is associated with appears.
    :param id_end: the optional end location in the assoc_id for locating the
        id from the assoc_id of a note of this type. This is only valid for
        items that have a fixed length key.
    :param default_subtype: the default sub_type specified upon creation of a
        note of this type.
    """

    def __init__(self, root, key_pattern_count, id_start,
                 id_end=None, default_subtype="metadata"):
        self.root = root
        self.base_pattern = "{}/".format(root)
        self.kp_count = key_pattern_count
        self.key_pattern = "{}{}".format(root, "/{}" * self.kp_count)
        self.lp_count = self.kp_count - 1 if self.kp_count > 0 else 0
        self.lookup_pattern = "{}/{}".format(root, "{}/" * self.lp_count)
        self.id_start = id_start
        self.id_end = id_end
        self.default_subtype = default_subtype


class NoteType(Enum):

    # Action
    #
    # Text:      action/12345678901234567890123456
    #                  |                         |
    # Position: 0....5.|..1....1....2....2....3..|.3
    #                  |  0    5    0    5    0  | 5
    #                  |                         |
    #           (7) ACTION_ID_START              |
    #                                      (33) ACTION_ID_END
    ACTION = _NoteType(
        root="action",
        key_pattern_count=1,
        id_start=7,
        id_end=33,
        default_subtype="action metadata")

    # Step
    #
    # Text:      step/12345678901234567890123456/my_step
    #                |                         ||
    # Position: 0....5....1....1....2....2....3||..3....4
    #                |    0    5    0    5    0||  5    0
    #                |                         |\
    #           (5) STEP_ACTION_ID_START       | \
    #                                          | (32) STEP_ID_START
    #                               (31) STEP_ACTION_ID_END
    STEP = _NoteType(
        root="step",
        key_pattern_count=2,
        id_start=32,
        default_subtype="step metadata")

    OTHER = _NoteType(root="", key_pattern_count=0, id_start=0)

    @property
    def base_pattern(self):
        return self.value.base_pattern

    @property
    def key_pattern(self):
        return self.value.key_pattern

    @property
    def lookup_pattern(self):
        return self.value.lookup_pattern

    @property
    def id_start(self):
        return self.value.id_start

    @property
    def id_end(self):
        return self.value.id_end

    @property
    def default_subtype(self):
        return self.value.default_subtype

    @classmethod
    def get_type(cls, note):
        for tp in cls:
            if note.assoc_id.startswith(tp.value.base_pattern):
                return tp
        return cls.OTHER


class NotesHelper:
    """Notes Helper

    Provides helper methods for the common use cases for notes
    :param notes_manager: the NotesManager object to use
    """
    def __init__(self, notes_manager):
        self.nm = notes_manager

    def _failsafe_make_note(self, assoc_id, subject, sub_type, note_val,
                            verbosity=MIN_VERBOSITY, link_url=None,
                            is_auth_link=None, note_timestamp=None):
        """LOG and continue on any note creation failure"""
        try:
            self.nm.create(
                assoc_id=assoc_id,
                subject=subject,
                sub_type=sub_type,
                note_val=note_val,
                verbosity=verbosity,
                link_url=link_url,
                is_auth_link=is_auth_link,
                note_timestamp=note_timestamp
            )
        except Exception as ex:
            LOG.warn(
                "Creating note for {} encountered a problem, exception info "
                "follows, but processing is not halted for notes.",
                assoc_id
            )
            LOG.exception(ex)

    def _failsafe_get_notes(self, assoc_id_pattern, verbosity,
                            exact_match):
        """LOG and continue on any note retrieval failure"""
        try:
            if verbosity < MIN_VERBOSITY:
                return []
            q = Query(assoc_id_pattern, verbosity, exact_match)
            return self.nm.retrieve(q)
        except Exception as ex:
            LOG.warn(
                "Note retrieval for {} encountered a problem, exception "
                "info follows, but processing is not halted for notes.",
                assoc_id_pattern
            )
            LOG.exception(ex)
        return []

    #
    # Retrieve notes by note ID
    #

    def get_note(self, note_id):
        """Return a single note looked up by the specified note_id

        :param note_id: the ULID of the note to retrieve.
        :raises NoteNotFoundError: if there is no note matching the requested
            note_id
        """
        return self.nm.retrieve_by_id(note_id)

    def get_note_details(self, note):
        """Return the note details for the specified note

        :param note: the Note object with additional details to retrieve.
        """
        return self.nm.get_note_url_info(note)

    def get_note_assoc_id_type(self, note):
        """Return the type of note based on the assoc_id

        :param note: The note to examine

        The purpose of this method is to use the standard formats (e.g.:
        action and step) supported by this helper to get the type of note.
        This value can be used by a client to enforce access rules to the note
        based on the item it is related to.
        """
        return NoteType.get_type(note)

    #
    # Action notes helper methods
    #

    def make_action_note(self, action_id, note_val, subject=None,
                         sub_type=None, verbosity=MIN_VERBOSITY, link_url=None,
                         is_auth_link=None, note_timestamp=None):
        """Creates an action note using a convention for the note's assoc_id

        :param action_id: the ULID id of an action
        :param note_val: the text for the note
        :param subject: optional subject for the note. Defaults to the
            action_id
        :param sub_type: optional subject type for the note, defaults to
            "action metadata"
        :param verbosity: optional verbosity for the note, defaults to 1,
            i.e.: summary level
        :param link_url: optional link URL if there's additional information
            to retreive from another source.
        :param is_auth_link: optional, defaults to False, indicating if there
            is a need to send a Shipyard service account token with the
            request to the optional URL
        :param note_timestamp: the parseable string timestamp to associate with
            this note. Optional, defaults to the creation time of the note.
        """
        assoc_id = NoteType.ACTION.key_pattern.format(action_id)
        if subject is None:
            subject = action_id
        if sub_type is None:
            sub_type = NoteType.ACTION.default_subtype

        self._failsafe_make_note(
            assoc_id=assoc_id,
            subject=subject,
            sub_type=sub_type,
            note_val=note_val,
            verbosity=verbosity,
            link_url=link_url,
            is_auth_link=is_auth_link,
            note_timestamp=note_timestamp
        )

    def get_all_action_notes(self, verbosity=MIN_VERBOSITY):
        """Retrieve notes for all actions, in a dictionary keyed by action id.

        :param verbosity: optional integer, 0-5, the maximum verbosity level
            to retrieve, defaults to 1 (most summary level)
            if set to less than 1, returns {}, skipping any retrieval
        """
        notes = self._failsafe_get_notes(
            assoc_id_pattern=NoteType.ACTION.lookup_pattern,
            verbosity=verbosity,
            exact_match=False
        )
        note_dict = {}
        id_s = NoteType.ACTION.id_start
        id_e = NoteType.ACTION.id_end
        for n in notes:
            action_id = n.assoc_id[id_s:id_e]
            if action_id not in note_dict:
                note_dict[action_id] = []
            note_dict[action_id].append(n)
        return note_dict

    def get_action_notes(self, action_id, verbosity=MAX_VERBOSITY):
        """Retrive notes related to a particular action

        :param action_id: the action for which to retrieve notes.
        :param verbosity: optional integer, 0-5, the maximum verbosity level
            to retrieve, defaults to 5 (most detailed level)
            if set to less than 1, returns [], skipping any retrieval

        """
        return self._failsafe_get_notes(
            assoc_id_pattern=NoteType.ACTION.key_pattern.format(action_id),
            verbosity=verbosity,
            exact_match=True
        )

    #
    # Step notes helper methods
    #

    def make_step_note(self, action_id, step_id, note_val, subject=None,
                       sub_type=None, verbosity=MIN_VERBOSITY, link_url=None,
                       is_auth_link=None, note_timestamp=None):
        """Creates an action note using a convention for the note's assoc_id

        :param action_id: the ULID id of the action containing the note
        :param step_id: the step for this note
        :param note_val: the text for the note
        :param subject: optional subject for the note. Defaults to the
            step_id
        :param sub_type: optional subject type for the note, defaults to
            "step metadata"
        :param verbosity: optional verbosity for the note, defaults to 1,
            i.e.: summary level
        :param link_url: optional link URL if there's additional information
            to retreive from another source.
        :param is_auth_link: optional, defaults to False, indicating if there
            is a need to send a Shipyard service account token with the
            request to the optional URL
        :param note_timestamp: the parseable string timestamp to associate with
            this note. Optional, defaults to the creation time of the note.
        """
        assoc_id = NoteType.STEP.key_pattern.format(action_id, step_id)
        if subject is None:
            subject = step_id
        if sub_type is None:
            sub_type = NoteType.STEP.default_subtype

        self._failsafe_make_note(
            assoc_id=assoc_id,
            subject=subject,
            sub_type=sub_type,
            note_val=note_val,
            verbosity=verbosity,
            link_url=link_url,
            is_auth_link=is_auth_link,
            note_timestamp=note_timestamp
        )

    def get_all_step_notes_for_action(self, action_id,
                                      verbosity=MIN_VERBOSITY):
        """Retrieve a dict keyed by step names for the action_id

        :param action_id: the action that contains the target steps
        :param verbosity: optional integer, 0-5, the maximum verbosity level
            to retrieve, defaults to 1 (most summary level)
            if set to less than 1, returns {}, skipping any retrieval
        """
        notes = self._failsafe_get_notes(
            assoc_id_pattern=NoteType.STEP.lookup_pattern.format(action_id),
            verbosity=verbosity,
            exact_match=False
        )
        note_dict = {}
        id_s = NoteType.STEP.id_start
        for n in notes:
            step_id = n.assoc_id[id_s:]
            if step_id not in note_dict:
                note_dict[step_id] = []
            note_dict[step_id].append(n)
        return note_dict

    def get_step_notes(self, action_id, step_id, verbosity=MAX_VERBOSITY):
        """Retrive notes related to a particular step

        :param action_id: the action containing the step
        :param step_id: the id of the step
        :param verbosity: optional integer, 0-5, the maximum verbosity level
            to retrieve, defaults to 5 (most detailed level)
            if set to less than 1, returns [], skipping any retrieval

        """
        return self._failsafe_get_notes(
            assoc_id_pattern=NoteType.STEP.key_pattern.format(
                action_id, step_id),
            verbosity=verbosity,
            exact_match=True
        )
