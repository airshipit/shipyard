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
"""ShipyardSQLNotesStorage

Implementation of NotesStorage that is based on the structure of the notes
table as defined in Shipyard. Accepts a SQLAlchemy engine as input, and
generates a model class from the notes table.

Mapping to/from Note objects is encapsulated here for a consistent interface
"""
from contextlib import contextmanager
import logging

from sqlalchemy import and_
from sqlalchemy import Column
from sqlalchemy import func
from sqlalchemy import Text
from sqlalchemy import types

from sqlalchemy.orm import declarative_base  # Updated import
from sqlalchemy.orm import sessionmaker

from .notes import Note
from .notes import NotesStorage
from .errors import NoteNotFoundError
from .errors import NotesError
from .errors import NotesInitializationError

LOG = logging.getLogger(__name__)
Base = declarative_base()  # Updated to use the new API


class TNote(Base):
    """Notes ORM class"""
    __tablename__ = 'notes'

    # These must align with the table defined using Alembic
    note_id = Column('note_id', types.String(26), primary_key=True)
    assoc_id = Column('assoc_id', types.String(128), nullable=False)
    subject = Column('subject', types.String(128), nullable=False)
    sub_type = Column('sub_type', types.String(128), nullable=False)
    note_val = Column('note_val', Text, nullable=False)
    verbosity = Column('verbosity', types.Integer, nullable=False)
    link_url = Column('link_url', Text, nullable=True)
    is_auth_link = Column('is_auth_link', types.Boolean, nullable=False)
    note_timestamp = Column('note_timestamp',
                            types.TIMESTAMP(timezone=True),
                            server_default=func.now())


class ShipyardSQLNotesStorage(NotesStorage):
    """SQL Alchemy implementation of a notes storage; Shipayrd table structure

    Accepts a SQL Alchemy Engine to serve as the connection to the persistence
    layer for Notes.

    :param engine_getter: A method that can be used to get SQLAlchemy engine
        to use
    """

    def __init__(self, engine_getter):
        try:
            self._engine_getter = engine_getter
            self._session = None
        except Exception as ex:
            LOG.exception(ex)
            raise NotesInitializationError(
                "Misconfiguration has casuse a failure to setup the desired "
                "database connection for Notes.")

    def _get_session(self):
        """Lazy initilize the sessionmaker, invoke the engine getter, and
        use it to return a session
        """
        if not self._session:
            self._session = sessionmaker(bind=self._engine_getter())
        return self._session()

    @contextmanager
    def session_scope(self):
        """Context manager for a SQLAlchemy session"""
        session = self._get_session()
        try:
            yield session
            session.commit()
        except Exception as ex:
            session.rollback()
            if isinstance(ex, NotesError):
                raise
            else:
                LOG.exception(ex)
                raise NotesError(
                    "An unexpected error has occurred while attempting to "
                    "interact with the database for note storage")
        finally:
            session.close()

    def store(self, note):
        """Store a note in the database"""
        r_note = None
        with self.session_scope() as session:
            tnote = self._map(note, TNote)
            session.add(tnote)
            r_note = self._map(tnote, Note)
        return r_note

    def retrieve(self, query):
        a_id_pat = query.assoc_id_pattern
        max_verb = query.max_verbosity
        r_notes = []
        with self.session_scope() as session:
            notes_res = []
            if (query.exact_match):
                n_qry = session.query(TNote).filter(
                    and_(TNote.assoc_id == a_id_pat,
                         TNote.verbosity <= max_verb)).order_by(
                             TNote.note_timestamp)
            else:
                n_qry = session.query(TNote).filter(
                    and_(TNote.assoc_id.like(a_id_pat + '%'),
                         TNote.verbosity <= max_verb)).order_by(
                             TNote.note_timestamp)
            db_notes = n_qry.all()
            for tn in db_notes:
                r_notes.append(self._map(tn, Note))
        return r_notes

    def retrieve_by_id(self, note_id):
        with self.session_scope() as session:
            note = session.query(TNote).filter(
                TNote.note_id == note_id).one_or_none()
            if not note:
                raise NoteNotFoundError()
            return self._map(note, Note)

    def _map(self, src, target_type):
        """Maps a Note object to/from a TNote object.

        :param src: the object to use as a source
        :param target_type: the type of object to create and map to
        """
        try:
            tgt = target_type(assoc_id=src.assoc_id,
                              subject=src.subject,
                              sub_type=src.sub_type,
                              note_val=src.note_val,
                              verbosity=src.verbosity,
                              link_url=src.link_url,
                              is_auth_link=src.is_auth_link,
                              note_id=src.note_id,
                              note_timestamp=src.note_timestamp)
        except AttributeError as ae:
            LOG.exception(ae)
            raise NotesError(
                "Note could not be translated from/to SQL form; mapping error")
        return tgt
