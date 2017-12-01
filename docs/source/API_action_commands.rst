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
#. Check deployed node status
    Checks that the deployment of nodes is successful.
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
