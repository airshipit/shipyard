..
      Copyright 2018 AT&T Intellectual Property.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _common_modules:

Helper Modules
==============

A home for the helper modules used by the various apis. While mostly the
helpers are used by the api that encompasses the function - e.g. configdocs
uses the configdocs helper, there are multiple cases where there's a need
to cross between functions. One such example is the need for the action
api's to need to use functionality related to configdocs. Rather than having
depenedencies between the functional sections, this package serves as a place
for the common dependencies encompassed into helper modules.

One major difference between the helpers and the api controllers is that
helpers should never raise API errors, but rather App Errors or other non-http
focused errors.

Note: The deckhand client module found in this package is intended to be
(largely) replaced by use of the Deckhand client, when that refactoring can
be accomplished.
