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

.. _site_definition_documents:

Site Definition Documents
=========================
Shipyard requires some documents to be loaded as part of the site definition
for the :ref:`deploy_site` and :ref:`update_site` as well as other workflows
that directly deal with site deployments.

Schemas
-------
-  `DeploymentConfiguration`_ schema
-  `DeploymentStrategy`_ schema

.. _deployment_configuration:

Deployment Configuration
------------------------
Allows for specification of configurable options used by the site deployment
related workflows, including the timeouts used for various steps, and the name
of the Armada manifest that will be used during the deployment/update.

A `sample deployment-configuration`_ shows a completely specified example.

`Default configuration values`_ are provided for most values.

Supported values
~~~~~~~~~~~~~~~~

-  Section: `physical_provisioner`:

  Values in the physical_provisioner section apply to the interactions with
  Drydock in the various steps taken to deploy or update bare-metal servers
  and networking.

  deployment_strategy
    The name of the deployment strategy document to be used. There is a default
    deployment strategy that is used if this field is not present.

  deploy_interval
    The seconds delayed between checks for progress of the step that performs
    deployment of servers.

  deploy_timeout
    The maximum seconds allowed for the step that performs deployment of all
    servers.

  destroy_interval
    The seconds delayed between checks for progress of destroying hardware
    nodes.

  destroy_timeout
    The maximum seconds allowed for destroying hardware nodes.

  join_wait
    The number of seconds allowed for a node to join the Kubernetes cluster.

  prepare_node_interval
    The seconds delayed between checks for progress of preparing nodes.

  prepare_node_timeout
    The maximum seconds allowed for preparing nodes.

  prepare_site_interval
    The seconds delayed between checks for progress of preparing the site.

  prepare_site_timeout
    The maximum seconds allowed for preparing the site.

  verify_interval
    The seconds delayed between checks for progress of verification.

  verify_timeout
    The maximum seconds allowed for verification by Drydock.

-  Section: `kubernetes_provisioner`:

  Values in the kubernetes_provisioner section apply to interactions with
  Promenade in the various steps of redeploying servers.

  drain_timeout
    The maximum seconds allowed for draining a node.

  drain_grace_period
    The seconds provided to Promenade as a grace period for pods to cease.

  clear_labels_timeout
    The maximum seconds provided to Promenade to clear labels on a node.

  remove_etcd_timeout
    The maximum seconds provided to Promenade to allow for removing etcd from
    a node.

  etcd_ready_timeout
    The maximum seconds allowed for etcd to reach a healthy state after
    a node is removed.

-  Section: `armada`:

  The Armada section provides configuration for the workflow interactions with
  Armada.

  manifest
    The name of the `Armada manifest document`_ that the workflow will use during
    site deployment activities. e.g.:'full-site'

.. _deployment_strategy:

Deployment Strategy
-------------------
The deployment strategy document is optionally specified in the
:ref:`deployment_configuration` and provides a way to group, sequence, and test
the deployments of groups of hosts deployed using `Drydock`_. A `sample
deployment-strategy`_ shows one possible strategy, in the context of the
Shipyard unit testing.

Using A Deployment Strategy
---------------------------
Defining a deployment strategy involves understanding the design of a site, and
the desired criticality of the nodes that make up the site.

A typical site may include a handful or many servers that participate in a
Kubernetes cluster. Several of the servers may serve as control nodes, while
others will handle the workload of the site. During the deployment of a site,
it may be critically important that some servers are operational, while others
may have a higher tolerance for misconfigured or failed nodes.

The deployment strategy provides a mechanism to handle defining groups of
nodes such that the criticality is reflected in the success criteria.

The name of the DeploymentStrategy document to use is defined in the
:ref:`deployment_configuration`, in the
``physical_provisioner.deployment_strategy`` field. The most simple deployment
strategy is used if one is not specified in the :ref:`deployment_configuration`
document for the site. Example::

  schema: shipyard/DeploymentStrategy/v1
  metadata:
    schema: metadata/Document/v1
    name: deployment-strategy
    layeringDefinition:
        abstract: false
        layer: global
    storagePolicy: cleartext
  data:
    groups: [
      - name: default
        critical: true
        depends_on: []
        selectors: [
          - node_names: []
            node_labels: []
            node_tags: []
            rack_names: []
        ]
        success_criteria:
          percent_successful_nodes: 100
    ]

-  This default configuration indicates that there are no selectors, meaning
   that all nodes in the design are included.
-  The criticality is set to ``true`` meaning that the workflow will halt if
   the success criteria are not met.
-  The success criteria indicates that all nodes must be succssful to consider
   the group a success.

In short, the default behavior is to deploy everything all at once, and halt
if there are any failures.

In a large deployment, this could be a problematic strategy as the chance of
success in one try goes down as complexity rises. A deployment strategy
provides a means to mitigate the unforeseen.

To define a deployment strategy, an example may be helpful, but first
definition of the fields follow:

Groups
~~~~~~
Groups are named sets of nodes that will be deployed together. The fields of a
group are:

name
  Required. The identifying name of the group.

critical
  Required. Indicates if this group is required to continue to additional
  phases of deployment.

depends_on
  Required, may be an empty list. Group names that must be successful before
  this group can be processed.

selectors
  Required, may be an empty list. A list of identifying information to indicate
  the nodes that are members of this group.

success_criteria
  Optional. Criteria that must evaluate to be true before a group is considered
  successfully complete with a phase of deployment.

Criticality
'''''''''''
-  Field: critical
-  Valid values: true | false

Each group is required to indicate true or false for the `critical` field.
This drives the behavior after the deployment of baremetal nodes.  If any
groups that are marked as `critical: true` fail to meet that group's success
criteria, the workflow will halt after the deployment of baremetal nodes. A
group that cannot be processed due to a parent dependency failing will be
considered failed, regardless of the success criteria.

Dependencies
''''''''''''
-  Field: depends_on
-  Valid values: [] or a list of group names

Each group specifies a list of depends_on groups, or an empty list. All
identified groups must complete successfully for the phase of deployment before
the current group is allowed to be processed by the current phase.

-  A failure (based on success criteria) of a group prevents any groups
   dependent upon the failed group from being attempted.
-  Circular dependencies will be rejected as invalid during document
   validation.
-  There is no guarantee of ordering among groups that have their dependencies
   met. Any group that is ready for deployment based on declared dependencies
   will execute, however execution of groups is serialized - two groups will
   not deploy at the same time.

Selectors
'''''''''
-  Field: selectors
-  Valid values: [] or a list of selectors

The list of selectors indicate the nodes that will be included in a group.
Each selector has four available filtering values: node_names, node_tags,
node_labels, and rack_names. Each selector is an intersection of this
critera, while the list of selectors is a union of the individual selectors.

-  Omitting a criterion from a selector, or using empty list means that
   criterion is ignored.
-  Having a completely empty list of selectors, or a selector that has no
   criteria specified indicates ALL nodes.
-  A collection of selectors that results in no nodes being identified will be
   processed as if 100% of nodes successfully deployed (avoiding division by
   zero), but would fail the minimum or maximum nodes criteria (still counts as
   0 nodes)
-  There is no validation against the same node being in multiple groups,
   however the workflow will not resubmit nodes that have already completed or
   failed in this deployment to Drydock twice, since it keeps track of each
   node uniquely. The success or failure of those nodes excluded from
   submission to Drydock will still be used for the success criteria
   calculation.

E.g.::

  selectors:
    - node_names:
        - node01
        - node02
      rack_names:
        - rack01
      node_tags:
        - control
    - node_names:
        - node04
      node_labels:
        - ucp_control_plane: enabled

Will indicate (not really SQL, just for illustration)::

    SELECT nodes
    WHERE node_name in ('node01', 'node02')
          AND rack_name in ('rack01')
          AND node_tags in ('control')
    UNION
    SELECT nodes
    WHERE node_name in ('node04')
          AND node_label in ('ucp_control_plane: enabled')

Success Criteria
''''''''''''''''
-  Field: success_criteria
-  Valid values: for possible values, see below

Each group optionally contains success criteria which is used to indicate if
the deployment of that group is successful. The values that may be specified:

percent_successful_nodes
  The calculated success rate of nodes completing the deployment phase.

  E.g.: 75 would mean that 3 of 4 nodes must complete the phase successfully.

  This is useful for groups that have larger numbers of nodes, and do not
  have critical minimums or are not sensitive to an arbitrary number of nodes
  not working.

minimum_successful_nodes
  An integer indicating how many nodes must complete the phase to be considered
  successful.

maximum_failed_nodes
  An integer indicating a number of nodes that are allowed to have failed the
  deployment phase and still consider that group successful.

When no criteria are specified, it means that no checks are done - processing
continues as if nothing is wrong.

When more than one criterion is specified, each is evaluated separately - if
any fail, the group is considered failed.

Example Deployment Strategy Document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This example shows a contrived deployment strategy with 5 groups:
control-nodes, compute-nodes-1, compute-nodes-2, monitoring-nodes,
and ntp-node.

::

  ---
  schema: shipyard/DeploymentStrategy/v1
  metadata:
    schema: metadata/Document/v1
    name: deployment-strategy
    layeringDefinition:
        abstract: false
        layer: global
    storagePolicy: cleartext
  data:
    groups:
      - name: control-nodes
        critical: true
        depends_on:
          - ntp-node
        selectors:
          - node_names: []
            node_labels: []
            node_tags:
              - control
            rack_names:
              - rack03
        success_criteria:
          percent_successful_nodes: 90
          minimum_successful_nodes: 3
          maximum_failed_nodes: 1
      - name: compute-nodes-1
        critical: false
        depends_on:
          - control-nodes
        selectors:
          - node_names: []
            node_labels: []
            rack_names:
              - rack01
            node_tags:
              - compute
        success_criteria:
          percent_successful_nodes: 50
      - name: compute-nodes-2
        critical: false
        depends_on:
          - control-nodes
        selectors:
          - node_names: []
            node_labels: []
            rack_names:
              - rack02
            node_tags:
              - compute
        success_criteria:
          percent_successful_nodes: 50
      - name: monitoring-nodes
        critical: false
        depends_on: []
        selectors:
          - node_names: []
            node_labels: []
            node_tags:
              - monitoring
            rack_names:
              - rack03
              - rack02
              - rack01
      - name: ntp-node
        critical: true
        depends_on: []
        selectors:
          - node_names:
              - ntp01
            node_labels: []
            node_tags: []
            rack_names: []
        success_criteria:
          minimum_successful_nodes: 1

The ordering of groups, as defined by the dependencies (``depends-on``
fields)::

   __________     __________________
  | ntp-node |   | monitoring-nodes |
   ----------     ------------------
       |
   ____V__________
  | control-nodes |
   ---------------
       |_________________________
           |                     |
     ______V__________     ______V__________
    | compute-nodes-1 |   | compute-nodes-2 |
     -----------------     -----------------

Given this, the order of execution could be any of the following:

- ntp-node > monitoring-nodes > control-nodes > compute-nodes-1 > compute-nodes-2
- ntp-node > control-nodes > compute-nodes-2 > compute-nodes-1 > monitoring-nodes
- monitoring-nodes > ntp-node > control-nodes > compute-nodes-1 > compute-nodes-2
- and many more ... the only guarantee is that ntp-node will run some time
  before control-nodes, which will run sometime before both of the
  compute-nodes. Monitoring-nodes can run at any time.

Also of note are the various combinations of selectors and the varied use of
success criteria.

Example Processing
''''''''''''''''''
Using the defined deployment strategy in the above example, the following is
an example of how it may process::

  Start
  |
  | prepare ntp-node           <SUCCESS>
  | deploy ntp-node            <SUCCESS>
  V
  | prepare control-nodes      <SUCCESS>
  | deploy control-nodes       <SUCCESS>
  V
  | prepare monitoring-nodes   <SUCCESS>
  | deploy monitoring-nodes    <SUCCESS>
  V
  | prepare compute-nodes-2    <SUCCESS>
  | deploy compute-nodes-2     <SUCCESS>
  V
  | prepare compute-nodes-1    <SUCCESS>
  | deploy compute-nodes-1     <SUCCESS>
  |
  Finish (success)

If there were a failure in preparing the ntp-node, the following would be the
result::

  Start
  |
  | prepare ntp-node           <FAILED>
  | deploy ntp-node            <FAILED, due to prepare failure>
  V
  | prepare control-nodes      <FAILED, due to dependency>
  | deploy control-nodes       <FAILED, due to dependency>
  V
  | prepare monitoring-nodes   <SUCCESS>
  | deploy monitoring-nodes    <SUCCESS>
  V
  | prepare compute-nodes-2    <FAILED, due to dependency>
  | deploy compute-nodes-2     <FAILED, due to dependency>
  V
  | prepare compute-nodes-1    <FAILED, due to dependency>
  | deploy compute-nodes-1     <FAILED, due to dependency>
  |
  Finish (failed due to critical group failed)

If a failure occurred during the deploy of compute-nodes-2, the following would
result::

  Start
  |
  | prepare ntp-node           <SUCCESS>
  | deploy ntp-node            <SUCCESS>
  V
  | prepare control-nodes      <SUCCESS>
  | deploy control-nodes       <SUCCESS>
  V
  | prepare monitoring-nodes   <SUCCESS>
  | deploy monitoring-nodes    <SUCCESS>
  V
  | prepare compute-nodes-2    <SUCCESS>
  | deploy compute-nodes-2     <FAILED, non critical group>
  V
  | prepare compute-nodes-1    <SUCCESS>
  | deploy compute-nodes-1     <SUCCESS>
  |
  Finish (success with some nodes/groups failed)

Important Points
~~~~~~~~~~~~~~~~
-  By default, the deployment strategy is all-at-once, requiring total success.
-  Critical group failures halt the deployment activity AFTER processing all
   nodes, but before proceeding to deployment of the software using Armada.
-  Success Criteria are evaluated at the end of processing of each of two
   phases for each group. A failure in a parent group indicates a failure for
   child groups - those children will not be processed.
-  Group processing is serial.

Interactions
~~~~~~~~~~~~
During the processing of nodes, the workflow interacts with Drydock using the
node filter mechanism provided in the Drydock API. When formulating the nodes
to process in a group, Shipyard will make an inquiry of Drydock's /nodefilter
endpoint to get the list of nodes that match the selectors for the group.

Shipyard will keep track of nodes that are actionable for each group using the
response from Drydock, as well as prior group inquiries. This means
that any nodes processed in a group will not be reprocessed in a later group,
but will still count toward that group's success criteria.

Two actions (prepare, deploy) will be invoked against Drydock during the actual
node preparation and deployment. The workflow will monitor the tasks created by
Drydock and keep track of the successes and failures.

At the end of processing, the workflow step will report the success status for
each group and each node. Processing will either stop or continue depending on
the success of critical groups.

Example beginning of group processing output from a workflow step::

   INFO     Setting group control-nodes with None -> Stage.NOT_STARTED
   INFO     Group control-nodes selectors have resolved to nodes: node2, node1
   INFO     Setting group compute-nodes-1 with None -> Stage.NOT_STARTED
   INFO     Group compute-nodes-1 selectors have resolved to nodes: node5, node4
   INFO     Setting group compute-nodes-2 with None -> Stage.NOT_STARTED
   INFO     Group compute-nodes-2 selectors have resolved to nodes: node7, node8
   INFO     Setting group spare-compute-nodes with None -> Stage.NOT_STARTED
   INFO     Group spare-compute-nodes selectors have resolved to nodes: node11, node10
   INFO     Setting group all-compute-nodes with None -> Stage.NOT_STARTED
   INFO     Group all-compute-nodes selectors have resolved to nodes: node11, node7, node4, node8, node10, node5
   INFO     Setting group monitoring-nodes with None -> Stage.NOT_STARTED
   INFO     Group monitoring-nodes selectors have resolved to nodes: node12, node6, node9
   INFO     Setting group ntp-node with None -> Stage.NOT_STARTED
   INFO     Group ntp-node selectors have resolved to nodes: node3
   INFO     There are no cycles detected in the graph

Of note is the resolution of groups to a list of nodes. Notice that the nodes
in all-compute-nodes node11 overlap the nodes listed as part of other groups.
When processing, if all the groups were to be processed before
all-compute-nodes, there would be no remaining nodes that are actionable when
the workflow tries to process all-compute-nodes. The all-compute-nodes groups
would then be evaluated for success criteria immediately against those nodes
processed prior. E.g.::

   INFO     There were no actionable nodes for group all-compute-nodes. It is possible that all nodes: [node11, node7, node4, node8, node10, node5] have previously been deployed. Group will be immediately checked against its success criteria
   INFO     Assessing success criteria for group all-compute-nodes
   INFO     Group all-compute-nodes success criteria passed
   INFO     Setting group all-compute-nodes with Stage.NOT_STARTED -> Stage.PREPARED
   INFO     Group all-compute-nodes has met its success criteria and is now set to stage Stage.PREPARED
   INFO     Assessing success criteria for group all-compute-nodes
   INFO     Group all-compute-nodes success criteria passed
   INFO     Setting group all-compute-nodes with Stage.PREPARED -> Stage.DEPLOYED
   INFO     Group all-compute-nodes has met its success criteria and is successfully deployed (Stage.DEPLOYED)

Example summary output from workflow step doing node processing::

   INFO     =====   Group Summary   =====
   INFO       Group monitoring-nodes ended with stage: Stage.DEPLOYED
   INFO       Group ntp-node [Critical] ended with stage: Stage.DEPLOYED
   INFO       Group control-nodes [Critical] ended with stage: Stage.DEPLOYED
   INFO       Group compute-nodes-1 ended with stage: Stage.DEPLOYED
   INFO       Group compute-nodes-2 ended with stage: Stage.DEPLOYED
   INFO       Group spare-compute-nodes ended with stage: Stage.DEPLOYED
   INFO       Group all-compute-nodes ended with stage: Stage.DEPLOYED
   INFO     ===== End Group Summary =====
   INFO     =====   Node Summary   =====
   INFO       Nodes Stage.NOT_STARTED:
   INFO       Nodes Stage.PREPARED:
   INFO       Nodes Stage.DEPLOYED: node11, node7, node3, node4, node2, node1, node12, node8, node9, node6, node10, node5
   INFO       Nodes Stage.FAILED:
   INFO     ===== End Node Summary =====
   INFO     All critical groups have met their success criteria

Overall success or failure of workflow step processing based on critical groups
meeting or failing their success criteria will be reflected in the same fashion
as any other workflow step output from Shipyard.

An Example of CLI `describe action` command output, with failed processing::

    $ shipyard describe action/01BZZK07NF04XPC5F4SCTHNPKN
    Name:                  deploy_site
    Action:                action/01BZZK07NF04XPC5F4SCTHNPKN
    Lifecycle:             Failed
    Parameters:            {}
    Datetime:              2017-11-27 20:34:24.610604+00:00
    Dag Status:            failed
    Context Marker:        71d4112e-8b6d-44e8-9617-d9587231ffba
    User:                  shipyard

    Steps                                                              Index        State
    step/01BZZK07NF04XPC5F4SCTHNPKN/dag_concurrency_check              1            success
    step/01BZZK07NF04XPC5F4SCTHNPKN/validate_site_design               2            success
    step/01BZZK07NF04XPC5F4SCTHNPKN/drydock_build                      3            failed
    step/01BZZK07NF04XPC5F4SCTHNPKN/armada_build                       4            None
    step/01BZZK07NF04XPC5F4SCTHNPKN/drydock_prepare_site               5            success
    step/01BZZK07NF04XPC5F4SCTHNPKN/drydock_nodes                      6            failed


.. _`Armada manifest document`: https://airshipit.readthedocs.io/projects/armada/en/latest/operations/guide-build-armada-yaml.html?highlight=manifest
.. _`Default configuration values`: https://git.airshipit.org/cgit/airship-shipyard/tree/src/bin/shipyard_airflow/shipyard_airflow/plugins/deployment_configuration_operator.py
.. _DeploymentConfiguration: https://git.airshipit.org/cgit/airship-shipyard/tree/src/bin/shipyard_airflow/shipyard_airflow/schemas/deploymentConfiguration.yaml
.. _DeploymentStrategy: https://git.airshipit.org/cgit/airship-shipyard/tree/src/bin/shipyard_airflow/shipyard_airflow/schemas/deploymentStrategy.yaml
.. _Drydock: https://git.airshipit.org/cgit/airship-drydock
.. _`sample deployment-configuration`: https://git.airshipit.org/cgit/airship-shipyard/tree/src/bin/shipyard_airflow/tests/unit/yaml_samples/deploymentConfiguration_full_valid.yaml
.. _`sample deployment-strategy`: https://git.airshipit.org/cgit/airship-shipyard/tree/src/bin/shipyard_airflow/tests/unit/yaml_samples/deploymentStrategy_full_valid.yaml
