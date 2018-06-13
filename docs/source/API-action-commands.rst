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

.. _deploy_site:

deploy_site
~~~~~~~~~~~

Triggers the initial deployment of a site, using the latest committed
configuration documents. Steps, conceptually:

#. Concurrency check
    Prevents concurrent site modifications by conflicting
    actions/workflows.
#. Preflight checks
    Ensures all Airship components are in a responsive state.
#. Validate design
    Asks each involved Airship component to validate the design. This ensures
    that the previously committed design is valid at the present time.
#. Drydock build
    Orchestrates the Drydock component to configure hardware and the
    Kubernetes environment (Drydock -> Promenade)
#. Armada build
    Orchestrates Armada to configure software on the nodes as designed.

.. _update_site:

update_site
~~~~~~~~~~~

Applies a new committed configuration to the environment. The steps of
update_site mirror those of :ref:`deploy_site`.

Actions under development
~~~~~~~~~~~~~~~~~~~~~~~~~

These actions are under active development

-  redeploy_server

  Using parameters to indicate which server(s) triggers a redeployment of those
  servers to the last-known-good design and secrets

Future actions
~~~~~~~~~~~~~~

These actions are anticipated for development

-  test region

  Invoke site validation testing - perhaps a baseline is an invocation of all
  component's exposed tests or extended health checks. This test would be used
  as a preflight-style test to ensure all components are in a working state.

-  test component

  Invoke a particular platform component to test it. This test would be
  used to interrogate a particular platform component to ensure it is in a
  working state, and that its own downstream dependencies are also
  operational
