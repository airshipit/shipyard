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
"""Coordination and running of the documents to validate for Shipyard"""
import logging

LOG = logging.getLogger(__name__)


class _DocValidationDef:
    """Represents the definition, status, and results of a validation

    :param validator: the class of the validator
    :param name: the name of the document to be validated
    """
    def __init__(self, validator, name):
        LOG.info("Setting up validation for %s", name)
        self.validator = validator
        self.name = name
        self.finished = False
        self.errored = False
        self.results = []


class DocumentValidationManager:
    """Coordinates the validation of Shipyard documents

    :param deckhand_client: An instance of a Deckhand client that can be used
        to interact with Deckhand during the validation
    :param revision: The numeric Deckhand revision of document under test
    :param validations: The list of tuples containing a Validator (extending
        DocumentValidator) and a document name.
    """
    def __init__(self, deckhand_client, revision, validations):
        self.deckhand_client = deckhand_client
        self.revision = revision
        self.validations = self._parse_validations(validations)
        self.errored = False
        self.validations_run = 0

    def _parse_validations(self, validations):
        # Turn tuples into DocValidationDefs
        defs = []
        for val, name in validations:
            defs.append(_DocValidationDef(val, name))
        return defs

    def validate(self):
        """Run the validations

        Runs through the validations until all are finished
        """
        unfinished = [v for v in self.validations if not v.finished]
        while unfinished:
            # find the next doc to validate
            for val_def in unfinished:
                vldtr = val_def.validator(deckhand_client=self.deckhand_client,
                                          revision=self.revision,
                                          doc_name=val_def.name)
                LOG.info("Validating document %s: %s ",
                         vldtr.schema, vldtr.doc_name)
                vldtr.validate()
                self.validations_run += 1
                # set the validation status from the status of the validator
                val_def.errored = vldtr.error_status
                val_def.results.extend(vldtr.val_msg_list)
                val_def.finished = True

                # acquire any new validations that should be run
                new_vals = self._parse_validations(vldtr.triggered_validations)
                self.validations.extend(new_vals)
            unfinished = [v for v in self.validations if not v.finished]

        # gather the results
        final_result = []
        for v in self.validations:
            if v.errored:
                self.errored = True
            final_result.extend(v.results)
        return final_result
