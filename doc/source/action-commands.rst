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

Example invocation
------------------

API input to create an action follows this pattern, varying the name field:

Without Parmeters::

  POST /v1.0/actions

  {"name" : "update_site"}

With Parameters::

  POST /v1.0/actions

  {
    "name": "redeploy_server",
    "parameters": {
      "target_nodes": ["node1", "node2"]
    }
  }

  POST /v1.0/actions

  {
    "name": "update_site",
    "parameters": {
      "continue-on-fail": "true"
    }
  }

Analogous CLI commands::

  shipyard create action update_site
  shipyard create action redeploy_server --param="target_nodes=node1,node2"
  shipyard create action update_site --param="continue-on-fail=true"

Supported actions
-----------------

These actions are currently supported using the Action API and CLI

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

.. _update_software:

update_software
~~~~~~~~~~~~~~~
Triggers an update of the software in a site, using the latest committed
configuration documents. Steps, conceptually:

#. Concurrency check
    Prevents concurrent site modifications by conflicting
    actions/workflows.
#. Validate design
    Asks each involved Airship component to validate the design. This ensures
    that the previously committed design is valid at the present time.
#. Armada build
    Orchestrates Armada to configure software on the nodes as designed.

.. _redeploy_server:

redeploy_server
~~~~~~~~~~~~~~~
Using parameters to indicate which server(s) triggers a teardown and
subsequent deployment of those servers to restore them to the current
committed design.

This action is a `target action`, and does not apply the `site action`
labels to the revision of documents in Deckhand. Application of site action
labels is reserved for site actions such as `deploy_site` and `update_site`.

Like other `target actions` that will use a baremetal or Kubernetes node as
a target, the `target_nodes` parameter will be used to list the names of the
nodes that will be acted upon.

Using redeploy_server
`````````````````````

.. danger::

   At this time, there are no safeguards with regard to the running workload
   in place before tearing down a server and the result may be *very*
   disruptive to a working site. Users are cautioned to ensure the server
   being torn down is not running a critical workload.
   To support controlling this, the Shipyard service allows actions to be
   associated with RBAC rules. A deployment of Shipyard can restrict access
   to this action to help prevent unexpected disaster.

Redeploying a server can have consequences to the running workload as noted
above. There are actions that can be taken by a deployment engineer or system
administrator before performing a redeploy_server to mitigate the risks and
impact.

There are three broad categories of nodes that can be considered in regard to
redeploy_server. It is possible that a node is both a Worker and a Control
node depending on the deployment of Airship:

#. Broken Node:

   A non-functional node, e.g. a host that has been corrupted to the point of
   being unable to participate in the Kubernetes cluster.

#. Worker Node:

   A node that is participating in the Kubernetes cluster not running
   control plane software, but providing capacity for workloads running in
   the environment.

#. Control Node:

   A node that is participating in the Kubernetes cluster and is hosting
   control plane software. E.g. Airship or other components that serve as
   controllers for the rest of the cluster in some way. These nodes may run
   software such as etcd or databases that contribute to the health of the
   overall Kubernetes cluster.

   Note that there is also the Genesis host, used to bootstrap the Airship
   platform. This node currently runs the Airship containers, including some
   that are not yet able to be migrated to other nodes, e.g. the MAAS rack
   controller, and disruptions arising from moving PostgreSQL.

.. important::

   Use of redeploy_server on the Airship Genesis host/node is not supported,
   and will result in serious disruption.

Yes
  Recommended step for this node type

No
  Generally not necessary for this node type

N/A
  Not applicable for this node type


+----------------------------------------+--------+--------+---------+
| Action                                 | Broken | Worker | Control |
+========================================+========+========+=========+
| Coordinate workload impacts with users | Yes    | Yes    | No      |
| [*]_                                   |        |        |         |
+----------------------------------------+--------+--------+---------+
|                                                                    |
+----------------------------------------+--------+--------+---------+
| Clear Kubernetes labels from the node  | N/A    | Yes    | Yes     |
| (for each label)                       |        |        |         |
+----------------------------------------+--------+--------+---------+
| ``$ kubectl label nodes <node> <label>-``                          |
+----------------------------------------+--------+--------+---------+
| Etcd - check for cluster health        | N/A    | N/A    | Yes     |
+----------------------------------------+--------+--------+---------+
| ``$ kubectl -n kube-system exec kubernetes-etcd-<hostname> etcdctl |
| member list``                                                      |
+----------------------------------------+--------+--------+---------+
| Drain Kubernetes node                  | N/A    | Yes    | Yes     |
+----------------------------------------+--------+--------+---------+
| ``$ kubectl drain <node>``                                         |
+----------------------------------------+--------+--------+---------+
| Disable the kubelet service            | N/A    | Yes    | Yes     |
+----------------------------------------+--------+--------+---------+
| ``$ systemctl stop kubelet``                                       |
|                                                                    |
| ``$ systemctl disable kubelet``                                    |
+----------------------------------------+--------+--------+---------+
| Remove node from Kubernetes            | Yes    | Yes    | Yes     |
+----------------------------------------+--------+--------+---------+
| ``$ kubectl delete node <node>``                                   |
+----------------------------------------+--------+--------+---------+
| Backup Disks (processes vary) [*]_     | Yes    | Yes    | Yes     |
+----------------------------------------+--------+--------+---------+
|                                                                    |
+----------------------------------------+--------+--------+---------+

.. [*] Of course it is up to the infrastructure operator if they wish to
   coordinate with their users. This guide assumes client or user
   communication as a common courtesy.

.. [*] Server redeployment will (quick) erase all disks during the process,
   but desired enhancements to redeploy_server may include options for disk
   handling. Situationally, it may not be necessary to backup disks if the
   underlying implementation already provides the needed resiliency and
   redundancy.

Future actions
~~~~~~~~~~~~~~

These actions are anticipated for development

test region
  Invoke site validation testing - perhaps a baseline is an invocation of all
  components' exposed tests or extended health checks. This test would be used
  as a preflight-style test to ensure all components are in a working state.

test component
  Invoke a particular platform component to test it. This test would be
  used to interrogate a particular platform component to ensure it is in a
  working state, and that its own downstream dependencies are also
  operational

update labels
  Triggers an update to the Kubernetes node labels for specified server(s)
