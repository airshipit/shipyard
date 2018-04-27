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
"""Utilities for use by document validators."""
import logging

from .errors import DocumentLookupError, DocumentNotFoundError

LOG = logging.getLogger(__name__)


class DocumentValidationUtils:
    def __init__(self, deckhand_client):
        if deckhand_client is None:
            raise TypeError('Deckhand client is required.')
        self.deckhand_client = deckhand_client

    def get_unique_doc(self, revision_id, name, schema):
        """Retrieve a single, unique document as a dictionary

        :param revision_id: the revision to fetch the rendered document from
        :param name: the name of the document
        :param schema: the schema for the document
        :param raise_ex: if True, raise an ApiError if the document is not
            found
        returns the specified document, or raises a DocumentLookupError
        """
        filters = {
            "schema": schema,
            "metadata.name": name
        }
        docs = self.get_docs_by_filter(revision_id, filters)
        LOG.info("Found %s documents", len(docs))
        if len(docs) == 1 and docs[0].data:
            return docs[0].data
        raise DocumentNotFoundError

    def get_docs_by_filter(self, revision_id, filters):
        """Get the dictionary form of documents from Deckhand using a filter

        :param revision_id: The revision to use
        :param filters: a dictionary containing the needed filters to get the
            needed documents
        Returns a list of dictionaries created from the rendered documents, or
        an empty list if they do not.
        """
        LOG.info("Attempting to retrieve %s from revision %s", str(filters),
                 revision_id)
        try:
            docs = self.deckhand_client.revisions.documents(revision_id,
                                                            rendered=True,
                                                            **filters)
        except Exception as ex:
            # If we looked for a document, it's either not there ([] response)
            # or it's there. Anything else is a DocumentLookupError.
            LOG.exception(ex)
            raise DocumentLookupError("Exception during lookup of a document "
                                      "for validation: {}".format(str(ex)))

        return docs or []
