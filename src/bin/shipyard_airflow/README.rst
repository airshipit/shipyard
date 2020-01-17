Shipyard
========

Shipyard is the directed acyclic graph controller for Kubernetes and
OpenStack control plane life cycle management, and a component of the
Airship Undercloud Platform (UCP).

Shipyard provides the entrypoint for the following aspects of the
control plane established by the Airship:

.. raw:: html

   <dl>

::

    <dt>
        Designs and Secrets
    </dt>
    <dd>
        Site designs, including the configuration of bare metal host
        nodes, network design, operating systems, Kubernetes nodes,
        Armada manifests, Helm charts, and any other descriptors that
        define the build out of a group of servers enter the Airship via
        Shipyard. Secrets, such as passwords and certificates use the
        same mechanism. <br />
        The designs and secrets are stored in Airship's Deckhand,
        providing for version history and secure storage among other
        document-based conveniences.
    </dd>
    <dt>
        Actions
    </dt>
    <dd>
        Interaction with the site's control plane is done via
        invocation of actions in Shipyard. Each action is backed by
        a workflow implemented as a directed acyclic graph (DAG) that
        runs using Apache Airflow. Shipyard provides a mechanism to
        monitor and control the execution of the workflow.
    </dd>

.. raw:: html

   </dl>

Find more documentation for Shipyard on `Read the
Docs <https://airship-shipyard.readthedocs.io>`__

Integration Points:
-------------------

| `OpenStack Identity
  (Keystone) <https://github.com/openstack/keystone>`__ provides
  authentication and support for role based authorization
| `Apache Airflow <https://airflow.incubator.apache.org/>`__ provides
  the framework and automation of workflows provided by Shipyard
| `PostgreSQL <https://www.postgresql.org/>`__ is used to persist
  information to correlate workflows with users and history of workflow
  commands
| `Deckhand <https://github.com/openstack/airship-deckhand>`__ supplies
  storage and management of site designs and secrets
| `Drydock <https://github.com/openstack/airship-drydock>`__ is
  orchestrated by Shipyard to perform bare metal node provisioning
| `Promenade <https://github.com/openstack/airship-promenade>`__ is
  indirectly orchestrated by Shipyard to configure and join Kubernetes
  nodes
| `Armada <https://github.com/openstack/airship-armada>`__ is
  orchestrated by Shipyard to deploy and test Kubernetes workloads

Getting Started:
----------------

| `Shipyard @ Openstack
  Gerrit <https://review.openstack.org/#/q/project:openstack/airship-shipyard>`__
| `Helm
  chart <https://github.com/openstack/airship-shipyard/tree/master/charts/shipyard>`__

See also:
---------

`Airship in a
Bottle <https://github.com/openstack/airship-in-a-bottle>`__
