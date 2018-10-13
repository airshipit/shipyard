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
import falcon

from shipyard_airflow.common.notes.errors import NoteNotFoundError
from shipyard_airflow.common.notes.errors import NoteURLNotSpecifiedError
from shipyard_airflow.common.notes.errors import NoteURLRetrievalError
from shipyard_airflow.common.notes.notes_helper import NoteType
from shipyard_airflow.control.base import BaseResource
from shipyard_airflow.control.helpers.notes import NOTES as notes_helper
from shipyard_airflow.errors import ApiError
from shipyard_airflow.errors import InvalidFormatError
from shipyard_airflow import policy


NOTE_TYPE_RBAC = {
    NoteType.ACTION: policy.GET_ACTION,
    NoteType.STEP: policy.GET_ACTION_STEP,
    # Anything else uses only the already checked GET_NOTEDETAILS
    # new known note types should be added to the notes helper and also
    # represented here.
    NoteType.OTHER: None
}


# /api/v1.0/notedetails/{note_id}
class NoteDetailsResource(BaseResource):
    """Resource to service requests for note details"""
    @policy.ApiEnforcer(policy.GET_NOTEDETAILS)
    def on_get(self, req, resp, **kwargs):
        """Retrieves additional information for a note.

        Using the specified note_id, looks up any additional information
        for a note
        """
        note_id = kwargs['note_id']
        self.validate_note_id(note_id)
        note = self.get_note_with_access_check(req.context, note_id)
        resp.body = self.get_note_details(note)
        resp.status = falcon.HTTP_200

    def validate_note_id(self, note_id):
        if not len(note_id) == 26:
            raise InvalidFormatError(
                title="Notes ID values are 26 character ULID values",
                description="Invalid note_id: {} in URL".format(note_id)
            )

    def get_note_with_access_check(self, context, note_id):
        """Retrieve the note and checks user access to the note

        :param context: the request context
        :param note_id: the id of the note to retrieve.
        :returns: the note
        """
        try:
            note = notes_helper.get_note(note_id)
            note_type = notes_helper.get_note_assoc_id_type(note)
            if note_type not in NOTE_TYPE_RBAC:
                raise ApiError(
                    title="Unable to check permission for note type",
                    description=(
                        "Shipyard is not correctly identifying note type "
                        "for note {}".format(note_id)),
                    status=falcon.HTTP_500,
                    retry=False)
            policy.check_auth(context, NOTE_TYPE_RBAC[note_type])
            return note
        except NoteNotFoundError:
            raise ApiError(
                title="No note found",
                description=("Note {} is not found".format(note_id)),
                status=falcon.HTTP_404)

    def get_note_details(self, note):
        """Retrieve the note details from the notes_helper

        :param note: the note with extended information
        """
        try:
            return notes_helper.get_note_details(note)
        except NoteURLNotSpecifiedError:
            raise ApiError(
                title="No further note details are available",
                description=("Note {} has no additional information to "
                             "return".format(note.note_id)),
                status=falcon.HTTP_404)
        except NoteURLRetrievalError:
            raise ApiError(
                title="Unable to retrieve URL information for note",
                description=("Note {} has additional information, but it "
                             "cannot be accessed by Shipyard at this "
                             "time".format(note.note_id)),
                status=falcon.HTTP_500)
