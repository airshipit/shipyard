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
#     action/12345678901234567890123456
# matching the patterns in this helper.
ACTION_KEY_PATTERN = "action/{}"
ACTION_LOOKUP_PATTERN = "action/"
ACTION_ID_START = 7
ACTION_ID_END = 33


class NotesHelper:
    """Notes Helper

    Provides helper methods for the common use cases for notes
    :param notes_manager: the NotesManager object to use
    """
    def __init__(self, notes_manager):
        self.nm = notes_manager

    def _failsafe_make_note(self, assoc_id, subject, sub_type, note_val,
                            verbosity=None, link_url=None, is_auth_link=None):
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

    def _failsafe_get_notes(self, assoc_id_pattern, max_verbosity,
                            exact_match):
        """LOG and continue on any note retrieval failure"""
        try:
            q = Query(assoc_id_pattern, max_verbosity, exact_match)
            return self.nm.retrieve(q)
        except Exception as ex:
            LOG.warn(
                "Note retrieval for {} encountered a problem, exception "
                "info follows, but processing is not halted for notes.",
                assoc_id_pattern
            )
            LOG.exception(ex)
        return []

    def make_action_note(self, action_id, note_val, subject=None,
                         sub_type=None, verbosity=None, link_url=None,
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
        if verbosity is None:
            verbosity = 1

        self._failsafe_make_note(
            assoc_id=assoc_id,
            subject=subject,
            sub_type=sub_type,
            note_val=note_val,
            verbosity=verbosity,
            link_url=link_url,
            is_auth_link=is_auth_link,
        )

    def get_all_action_notes(self, verbosity=None):
        """Retrieve notes for all actions, in a dictionary keyed by action id.

        :param verbosity: optional, 1-5, the maximum verbosity level to
            retrieve, defaults to 1 (most summary level)

        Warning: if there are a lot of URL links in notes, this could take a
        long time. The default verbosity of 1 attempts to avoid this as there
        is less expectation of URL links on summary notes.
        """
        max_verbosity = verbosity or MIN_VERBOSITY
        notes = self._failsafe_get_notes(
            assoc_id_pattern=ACTION_LOOKUP_PATTERN,
            max_verbosity=verbosity,
            exact_match=False
        )
        note_dict = {}
        for n in notes:
            # magic numbers [7:33] to slice a string like:
            #     action/12345678901234567890123456/something
            # matching the convention in this helper.
            # in the case where there are non-compliant, the slice will make
            # the action_id a garbage key and that note will not be easily
            # associated.
            action_id = n.assoc_id[ACTION_ID_START:ACTION_ID_END]
            if action_id not in note_dict:
                note_dict[action_id] = []
            note_dict[action_id].append(n)
        return note_dict

    def get_action_notes(self, action_id, verbosity=None):
        """Retrive notes related to a particular action

        :param action_id: the action for which to retrieve notes.
        :param verbosity: optional, 1-5, the maximum verbosity level to
            retrieve, defaults to 5 (most detailed level)
        """
        assoc_id_pattern = ACTION_KEY_PATTERN.format(action_id)
        max_verbosity = verbosity or MAX_VERBOSITY
        exact_match = True
        return self._failsafe_get_notes(
            assoc_id_pattern=assoc_id_pattern,
            max_verbosity=max_verbosity,
            exact_match=exact_match
        )
