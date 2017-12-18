..
      Copyright 2017 AT&T Intellectual Property.
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

.. _shipyard_action_commands:

Action Commands
===============

Supported actions
-----------------

These actions are currently supported using the Action API

deploy_site
~~~~~~~~~~~

Triggers the initial deployment of a site, using the latest committed
configuration documents. Steps:

#. Concurrency check
    Prevents concurrent site modifications by conflicting
    actions/workflows.
#. Preflight checks
    Ensures all UCP components are in a responsive state.
#. Get design version
    Uses Deckhand to discover the latest committed version of design for
    the site.
#. Validate design
    Asks each involved UCP component to validate the design. This ensures
    that the previously committed design is valid at the present time.
#. Drydock build
    Orchestrates the Drydock component to configure hardware and the
    Kubernetes environment (Drydock -> Promenade)
#. Armada build
    Orchestrates Armada to configure software on the nodes as designed.


Actions under development
~~~~~~~~~~~~~~~~~~~~~~~~~

These actions are under active development

-  update_site

  Triggers the initial deployment of a site, using the latest committed
  configuration documents. Steps: (a superset of deploy_site)

-  redeploy_server

  Using parameters to indicate which server(s), triggers a redeployment of
  server to the last known good design and secrets

Future actions
~~~~~~~~~~~~~~

These actions are anticipated for development

- test region

  Invoke site validation testing - perhaps baseline is a invocation of all
  components regular “component” tests. This test would be used as a
  preflight-style test to ensure all components are in a working state.

-  test component

  Invoke a particular platform component to test it. This test would be
  used to interrogate a particular platform component to ensure it is in a
  working state, and that its own downstream dependencies are also
  operational
