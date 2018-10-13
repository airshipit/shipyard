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
"""Notes

A reusable component allowing for recording and retreiving information related
to arbitrarily useage-based keys (the usage makes the association keys to their
string-based liking). The intention for Notes is generally for additional
non-fielded information that may be of interest to a user. Notes are not
intended to store info that would drive code paths or decisions. This is not
an arbitrary use key-value database.
"""
import abc
from datetime import datetime
import logging

import requests
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
import ulid

from .errors import NoteURLNotSpecifiedError
from .errors import NoteURLRetrievalError
from .errors import NotesInitializationError
from .errors import NotesRetrievalError
from .errors import NotesStorageError

LOG = logging.getLogger(__name__)
MAX_VERBOSITY = 5
MIN_VERBOSITY = 1


class NotesManager:
    """Interface to store and retrieve notes

    :param storage: A NotesStorage object to store and retrieve notes for a
        specific storage mechanism. e.g. Database, Service
    :param get_token: A method that returns an auth token that will be used
        as the X-Auth-Token header when resolving url-based notes
    :param connect_timeout: optional, The maximum time waiting to connect to
        a URL. Defaults to 3 seconds
    :param read_timeout: optional, The maximum time waiting to read the info
        from a URL. Defaults to 10 seconds

    Example usage:
        nm = NotesManager(SQLNotesStorage("connection_info"), get_url)
        a_note = nm.store(Note(...params...))
        notes = list(nm.retrieve(Query("some/id")))
    """
    def __init__(self, storage, get_token, connect_timeout=None,
                 read_timeout=None):
        if not isinstance(storage, NotesStorage):
            raise NotesInitializationError(
                "Storage object is not suitable for use with Notes"
            )
        self.storage = storage
        LOG.info(
            "Initializing Notes with storage mechanism: %s",
            storage.__class__.__name__
        )

        if not callable(get_token):
            raise NotesInitializationError(
                "Parameter get_token is not suitable for use with Notes. "
                "Must be a callable."
            )
        self.get_token = get_token

        # connect and read timeouts default to 3 and 10 seconds
        self.connect_timeout = connect_timeout or 3
        self.read_timeout = read_timeout or 10

    def create(self, assoc_id, subject, sub_type, note_val,
               verbosity=None, link_url=None, is_auth_link=None,
               note_id=None, note_timestamp=None, store=True):
        """Creates and stores a Note object from parameters

        Passthrough helper method to avoid additional imports for the Note
        class. Most of the parameters match that of the Note constructor.
        See: func:`notes.Note.__init__`
        Additional Parameters:

        :param store: optinal, default=True, invoke the store method
            immediately upon creation, if true
        """
        n = Note(assoc_id, subject, sub_type, note_val,
                 verbosity=verbosity, link_url=link_url,
                 is_auth_link=is_auth_link, note_id=note_id,
                 note_timestamp=note_timestamp)
        if store:
            return self.store(n)
        else:
            return n

    def store(self, note):
        """Store a note

        :param note: A Note object to store
        :returns: The note, as it was after storage
        """
        if note.verbosity < MIN_VERBOSITY or note.verbosity > MAX_VERBOSITY:
            raise NotesStorageError(
                "Verbosity of notes must range from {} "
                "to {} (most verbose)".format(MIN_VERBOSITY, MAX_VERBOSITY))
        try:
            return self.storage.store(note)
        except NotesStorageError:
            raise
        except Exception as ex:
            LOG.exception(ex)
            raise NotesStorageError("Unhandled error during storage of a note")

    def retrieve(self, query):
        """Retrieve a list of notes

        :param query: a query object to retrieve notes
        :returns: a list of notes matchin the query, or [] if there are no
            notes matching the query.
        """
        try:
            notes = list(self.storage.retrieve(query))
        except NotesRetrievalError:
            raise
        except Exception as ex:
            LOG.exception(ex)
            raise NotesRetrievalError(
                "Unhandled error during retrieval of notes"
            )
        for note in notes:
            if note.link_url:
                note.resolved_url_value = (
                    "Details at notedetails/{}".format(note.note_id))
        return notes

    def retrieve_by_id(self, note_id):
        """Return a single note looked up by the specified note_id

        :param note_id: the ULID of the note to retrieve.
        :raises NoteNotFoundError: if there is no note matching the requested
            note_id
        """
        return self.storage.retrieve_by_id(note_id)

    def get_note_url_info(self, note):
        """Resolve and return the value obtained from the URL for a Note.

        :param note: the note object or id of the note to retreive and set the
           value for.
        :returns: The contents retrieved from the note's URL.
        :raises NoteNotFoundError: when the note (id) specified does not match
            a known note
        :raises NoteURLNotSpecifiedError: when the note has no url specified
        :raises NoteURLRetrievalError: when there is an error using the
            note's specified URL.
        """
        # if the note is not a note, try to fetch it like an ID
        if not isinstance(note, Note):
            note = self.retrieve_by_id(note)
        if not note.link_url:
            LOG.debug("Note %s has no URL to resolve.", note.note_id)
            raise NoteURLNotSpecifiedError()

        auth_token = self.get_token()
        contents = None
        try:
            headers = {}

            # Don't pass credentials if not needed.
            if note.is_auth_link:
                headers['X-Auth-Token'] = auth_token

            response = requests.get(
                note.link_url,
                headers=headers,
                timeout=(self.connect_timeout, self.read_timeout))
            response.raise_for_status()

            # Set the valid response text to the note
            return response.text

        except (HTTPError, RequestException) as lookup_err:
            LOG.exception(lookup_err)
            raise NoteURLRetrievalError()


class Note:
    """Model object representing a note

    :param assoc_id: arbitrary value like action/xxxxxxx or
        step/xxxxxxx/step_name, useful for lookup, set by note creator
        Limit: 128 characters
    :param subject: arbitrary value to be used as the subject of the note,
        useful to a human e.g. mtn15r11n0001, set by note creator
        Limit: 128 characters
    :param sub_type: arbitrary value used to qualify the subject of the note,
        e.g. Node, Action, Step, set by note creator
        Limit: 128 characters
    :param note_val: the text value of the note, the contents of info to be
        displayed as note
    :param link_url: optional url that should be followed when the note is
        retrieved to append to its value
    :param is_auth_link: boolean if Shipyard's service ID auth credentials are
        needed to make the call to follow the link default=false
    :param verbosity: integer, 1-5 indicating the verbosity level, default = 1
    :param note_id: ULID that uniquely represents a note. Users are not
        expected to pass a value for the ID of a note, it will be assigned
    :param note_timestamp: String representation of the timestamp for the note
    """
    def __init__(self, assoc_id, subject, sub_type, note_val,
                 verbosity=None, link_url=None, is_auth_link=None,
                 note_id=None, note_timestamp=None):
        self.assoc_id = assoc_id
        self.subject = subject
        self.sub_type = sub_type
        self.note_val = note_val
        self.verbosity = verbosity or MIN_VERBOSITY
        self.link_url = link_url
        self.is_auth_link = is_auth_link or False
        self.note_id = note_id or ulid.ulid()
        self.note_timestamp = note_timestamp or str(datetime.utcnow())
        self._resolved_url_value = None

    @property
    def resolved_url_value(self):
        return self._resolved_url_value

    @resolved_url_value.setter
    def resolved_url_value(self, value):
        self._resolved_url_value = value

    def view(self):
        """Returns the user-facing dictionary version of the Note"""
        return {
            'assoc_id': self.assoc_id,
            'subject': self.subject,
            'sub_type': self.sub_type,
            'note_val': self.note_val,
            'verbosity': self.verbosity,
            'note_id': self.note_id,
            'note_timestamp': self.note_timestamp,
            'resolved_url_value': self.resolved_url_value,
        }


class Query:
    """Model object for a query to retrieve notes

    :param assoc_id_pattern: The pattern to match to the assoc_id for a note.
    :param max_verbosity: optional integer 1-5, defaults to 5 (everything)
    :param exact_match: boolean, defaults to False. If true, the
        assoc_id_pattern will be used precisely, otherwise assoc_id_pattern
        will be matched to the start of the assoc_id for notes.
    """
    def __init__(self, assoc_id_pattern, max_verbosity=None, exact_match=None):
        self.assoc_id_pattern = assoc_id_pattern
        self.max_verbosity = max_verbosity or MAX_VERBOSITY
        self.exact_match = exact_match or False


class NotesStorage(metaclass=abc.ABCMeta):
    """NotesStorage abstract base class

    Defines the interface for NotesStorage implementations that provide the
    specific mappings of Note objects to the target data store.
    """
    @abc.abstractmethod
    def store(self, note):
        """Store a Note object, return the note object as stored

        :param note: a Note object
        :returns: A single Note object, as was persisted.
        :raises NotesStorageError: When there is a failure to create the note.
        """
        pass

    @abc.abstractmethod
    def retrieve(self, query):
        """Query for a list of Note objects

        :param query: a Notes Query object representing the notes to be
            retrieved.
        :returns: List of Note objects matching the query
        :raises NotesRetrievalError: when there is a failure to retrieve notes,
            however an empty list is expected to be returned in the case of no
            results.
        """
        pass

    @abc.abstractmethod
    def retrieve_by_id(self, note_id):
        """Lookup a note by note_id

        :param note_id: The ID of the note to retrieve
        :returns: a single Note object matching the id or None if there is no
            note matching the ID.
        :raises NotesRetrievalError: if there is a failure to retrieve the
            note
        """
        pass
