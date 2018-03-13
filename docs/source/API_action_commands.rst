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
configuration documents. Steps, conceptually:

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

update_site
~~~~~~~~~~~

Applies a new committed configuration to the environment. The steps of
update_site mirror those of deploy_site.

Actions under development
~~~~~~~~~~~~~~~~~~~~~~~~~

These actions are under active development

-  redeploy_server

  Using parameters to indicate which server(s), triggers a redeployment of
  server to the last known good design and secrets

Future actions
~~~~~~~~~~~~~~

These actions are anticipated for development

-  test region

  Invoke site validation testing - perhaps baseline is a invocation of all
  components regular “component” tests. This test would be used as a
  preflight-style test to ensure all components are in a working state.

-  test component

  Invoke a particular platform component to test it. This test would be
  used to interrogate a particular platform component to ensure it is in a
  working state, and that its own downstream dependencies are also
  operational

Configuration Documents
-----------------------
Shipyard requires some configuration documents to be loaded into the
environment for the deploy_site and update_site as well as other workflows
that directly deal with site deployments.

Schemas
~~~~~~~
DeploymentConfiguration_ schema - Provides for validation of the
deployment-configuration documents

Documents
~~~~~~~~~
deployment-configuration - Allows for specification of configurable options
used by the site deployment related workflows, including the timeouts used for
various steps, and the name of the armada manifest that will be used during the
deployment/update.

A `sample deployment-configuration`_ shows a completely specified example.

`Default configuration values`_ are provided for most values.

Supported values:
'''''''''''''''''

-  physical_provisioner:

  Values in the physical_provisioner section apply to the interactions with
  Drydock in the various steps taken to deploy or update bare-metal servers
  and networking.

  -  deployment_strategy:

    Not currently used, placeholder for specifying how server deployments
    should be grouped. (e.g. all-at-once, by-rack, by-label)

  -  deploy_interval:

    The seconds delayed between checks for progress of the step that performs
    deployment of servers.

  -  deploy_timeout:

    The maximum seconds allowed for the step that performs deployment of all
    servers.

  -  destroy_interval:

    The seconds delayed between checks for progress of destroying hardware
    nodes.

  -  destroy_timeout:

    The maximum seconds allowed for destroying hardware nodes.

  -  join_wait:

    The number of seconds allowed for a node to join the Kubernetes cluster.

  -  prepare_node_interval:

    The seconds delayed between checks for progress of preparing nodes.

  -  prepare_node_timeout:

    The maximum seconds allowed for preparing nodes.

  -  prepare_site_interval:

    The seconds delayed between checks for progress of preparing the site.

  -  prepare_site_timeout:

    The maximum seconds allowed for preparing the site.

  -  verify_interval:

    The seconds delayed between checks for progress of verification.

  -  verify_timeout:

    The maximum seconds allowed for verification by Drydock.

-  kubernetes_provisioner:

  Values in the kubernetes_provisioner section apply to interactions with
  Promenade in the various steps of redeploying servers.

  -  drain_timeout:

    The maximum seconds allowed for draining a node.

  -  drain_grace_period:

    The seconds provided to Promenade as a grace period for pods to cease.

  -  clear_labels_timeout:

    The maximum seconds provided to Promenade to clear labels on a node.

  -  remove_etcd_timeout:

    The maximum seconds provided to Promenade to allow for removing etcd from
    a node.

  -  etcd_ready_timeout:

    The maximum seconds allowed for etcd to reach a healthy state after
    a node is removed.

-  armada:

  The armada section provides configuration for the workflow interactions with
  Armada.

  -  manifest:

    The name of the Armada manifest document that the workflow will use during
    site deployment activities. e.g.:'full-site'

.. _DeploymentConfiguration: https://github.com/att-comdev/shipyard/blob/master/shipyard_airflow/schemas/deploymentConfiguration.yaml
.. _`sample deployment-configuration`: https://github.com/att-comdev/shipyard/blob/master/tests/unit/yaml_samples/deploymentConfiguration_full_valid.yaml
.. _`Default configuration values`: https://github.com/att-comdev/shipyard/blob/a88a5cf15a81de32707fee49d7a626908a8c8f38/shipyard_airflow/plugins/deployment_configuration_operator.py#L47
