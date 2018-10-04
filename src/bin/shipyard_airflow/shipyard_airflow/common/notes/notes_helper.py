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
import logging

from .notes import MAX_VERBOSITY
from .notes import MIN_VERBOSITY
from .notes import Query

LOG = logging.getLogger(__name__)

# Constants and magic numbers for actions:
# [7:33] to slice a string like:
#
# Text:      action/12345678901234567890123456
#                  |                         |
# Position: 0....5.|..1....1....2....2....3..|.3
#                  |  0    5    0    5    0  | 5
#                  |                         |
#           (7) ACTION_ID_START              |
#                                      (33) ACTION_ID_END
#
# matching the patterns in this helper.
#
ACTION_KEY_PATTERN = "action/{}"
ACTION_LOOKUP_PATTERN = "action/"
ACTION_ID_START = 7
ACTION_ID_END = 33

# Constants and magic numbers for steps:
# [32:] to slice a step name pattern
#     step/{action_id}/{step_name}
#
# Text:      step/12345678901234567890123456/my_step
# Position: 0....5....1....1....2....2....3||..3....4
#                |    0    5    0    5    0||  5    0
#                |                         |\
#           (5) STEP_ACTION_ID_START       | \
#                                          | (32) STEP_ID_START
#                               (31) STEP_ACTION_ID_END
#
STEP_KEY_PATTERN = "step/{}/{}"
STEP_LOOKUP_PATTERN = "step/{}"
STEP_ACTION_ID_START = 5
STEP_ACTION_ID_END = 31
STEP_ID_START = 32


class NotesHelper:
    """Notes Helper

    Provides helper methods for the common use cases for notes
    :param notes_manager: the NotesManager object to use
    """
    def __init__(self, notes_manager):
        self.nm = notes_manager

    def _failsafe_make_note(self, assoc_id, subject, sub_type, note_val,
                            verbosity=MIN_VERBOSITY, link_url=None,
                            is_auth_link=None):
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
    # Action notes helper methods
    #

    def make_action_note(self, action_id, note_val, subject=None,
                         sub_type=None, verbosity=MIN_VERBOSITY, link_url=None,
                         is_auth_link=None):
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
        """
        assoc_id = ACTION_KEY_PATTERN.format(action_id)
        if subject is None:
            subject = action_id
        if sub_type is None:
            sub_type = "action metadata"

        self._failsafe_make_note(
            assoc_id=assoc_id,
            subject=subject,
            sub_type=sub_type,
            note_val=note_val,
            verbosity=verbosity,
            link_url=link_url,
            is_auth_link=is_auth_link,
        )

    def get_all_action_notes(self, verbosity=MIN_VERBOSITY):
        """Retrieve notes for all actions, in a dictionary keyed by action id.

        :param verbosity: optional integer, 0-5, the maximum verbosity level
            to retrieve, defaults to 1 (most summary level)
            if set to less than 1, returns {}, skipping any retrieval

        Warning: if there are a lot of URL links in notes, this could take a
        long time. The default verbosity of 1 attempts to avoid this as there
        is less expectation of URL links on summary notes.
        """
        notes = self._failsafe_get_notes(
            assoc_id_pattern=ACTION_LOOKUP_PATTERN,
            verbosity=verbosity,
            exact_match=False
        )
        note_dict = {}
        for n in notes:
            action_id = n.assoc_id[ACTION_ID_START:ACTION_ID_END]
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
            assoc_id_pattern=ACTION_KEY_PATTERN.format(action_id),
            verbosity=verbosity,
            exact_match=True
        )

    #
    # Step notes helper methods
    #

    def make_step_note(self, action_id, step_id, note_val, subject=None,
                       sub_type=None, verbosity=MIN_VERBOSITY, link_url=None,
                       is_auth_link=None):
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
        """
        assoc_id = STEP_KEY_PATTERN.format(action_id, step_id)
        if subject is None:
            subject = step_id
        if sub_type is None:
            sub_type = "step metadata"

        self._failsafe_make_note(
            assoc_id=assoc_id,
            subject=subject,
            sub_type=sub_type,
            note_val=note_val,
            verbosity=verbosity,
            link_url=link_url,
            is_auth_link=is_auth_link,
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
            assoc_id_pattern=STEP_LOOKUP_PATTERN.format(action_id),
            verbosity=verbosity,
            exact_match=False
        )
        note_dict = {}
        for n in notes:
            step_id = n.assoc_id[STEP_ID_START:]
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
            assoc_id_pattern=STEP_KEY_PATTERN.format(action_id, step_id),
            verbosity=verbosity,
            exact_match=True
        )
