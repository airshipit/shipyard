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
"""The design reference is a commonly used object across most of the undercloud
platform, particularly for use during validations of documents by each
component.
"""
import json

from shipyard_airflow.control.helpers.deckhand_client import (DeckhandClient,
                                                              DeckhandPaths)


class DesignRefHelper:

    def __init__(self):
        self._path = DeckhandClient.get_path(
            DeckhandPaths.RENDERED_REVISION_DOCS)

    def get_design_reference(self, revision_id):
        """Constructs a design reference as json using the supplied revision_id

        :param revision_id: the numeric Deckhand revision
        Returns a json String
        """
        return json.dumps(self.get_design_reference_dict(revision_id))

    def get_design_reference_href(self, revision_id):
        """Returns only the href to the deckhand design"""
        return "deckhand+{}".format(self._path.format(revision_id))

    def get_design_reference_dict(self, revision_id):
        """Constructs a Deckhand specific design reference

        :param revision_id: the numeric Deckhand revision
        Returns a dictionary representing the design_ref
        """
        return {
            "rel": "design",
            "href": self.get_design_reference_href(revision_id),
            "type": "application/x-yaml"
        }
