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
"""Tests for redaction functionality

- redaction_formatter
- redactor
"""
import logging
import sys

from shipyard_airflow.control.logging.redaction_formatter import (
    RedactionFormatter
)
from shipyard_airflow.control.util.redactor import Redactor


class TestRedaction():

    def test_redactor(self):
        redactor = Redactor()

        to_redact = "My password = swordfish"
        expected = "My password = ***"
        assert redactor.redact(to_redact) == expected

        # not a detected pattern - should be same
        to_redact = "My pass = swordfish"
        expected = "My pass = swordfish"
        assert redactor.redact(to_redact) == expected

        # yaml format
        to_redact = "My password: swordfish"
        expected = "My password: ***"
        assert redactor.redact(to_redact) == expected

        # yaml format
        to_redact = "My password: swordfish is not for sale"
        expected = "My password: *** is not for sale"
        assert redactor.redact(to_redact) == expected

        to_redact = """
password:
  swordfish
"""
        expected = """
password:
  ***
"""
        assert redactor.redact(to_redact) == expected

        to_redact = """
password:
  swordfish
  trains:
    cheese
"""
        expected = """
password:
  ***
  trains:
    cheese
"""
        assert redactor.redact(to_redact) == expected

    def test_extended_keys_redactor(self):
        redactor = Redactor(redaction="++++", keys=['trains'])
        to_redact = """
password:
  swordfish
  trains:
    cheese
"""
        expected = """
password:
  ++++
  trains:
    ++++
"""
        assert redactor.redact(to_redact) == expected

    def test_redaction_formatter(self, caplog):
        # since root logging is setup by prior tests need to remove all
        # handlers to simulate a clean environment of setting up this
        # RedactionFormatter
        for handler in list(logging.root.handlers):
            if not "LogCaptureHandler" == handler.__class__.__name__:
                logging.root.removeHandler(handler)

        logging.basicConfig(level=logging.DEBUG,
                            handlers=[logging.StreamHandler(sys.stdout)])
        for handler in logging.root.handlers:
            handler.setFormatter(RedactionFormatter(handler.formatter))
        logging.info('Established password: albatross for this test')
        assert 'albatross' not in caplog.text
        assert 'Established password: *** for this test' in caplog.text
