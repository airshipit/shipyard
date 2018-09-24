# Shipyard
Shipyard is the directed acyclic graph controller for Kubernetes and
OpenStack control plane life cycle management, and a component of the
Airship Undercloud Platform (UCP).

Shipyard provides the entrypoint for the following aspects of the
control plane established by the Airship:

<dl>
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
</dl>

Find more documentation for Shipyard on
[Read the Docs](https://airship-shipyard.readthedocs.io)


## Integration Points:
[OpenStack Identity (Keystone)](https://github.com/openstack/keystone)
provides authentication and support for role based authorization
\
[Apache Airflow](https://airflow.incubator.apache.org/) provides the
framework and automation of workflows provided by Shipyard
\
[PostgreSQL](https://www.postgresql.org/) is used to persist
information to correlate workflows with users and history of workflow
commands
\
[Deckhand](https://github.com/openstack/airship-deckhand) supplies storage
and management of site designs and secrets
\
[Drydock](https://github.com/openstack/airship-drydock) is orchestrated by
Shipyard to perform bare metal node provisioning
\
[Promenade](https://github.com/openstack/airship-promenade) is indirectly
orchestrated by Shipyard to configure and join Kubernetes nodes
\
[Armada](https://github.com/openstack/airship-armada) is orchestrated by
Shipyard to deploy and test Kubernetes workloads


## Getting Started:

[Shipyard @ Openstack Gerrit](https://review.openstack.org/#/q/project:openstack/airship-shipyard)
\
[Helm chart](https://github.com/openstack/airship-shipyard/tree/master/charts/shipyard)


## See also:

[Airship in a Bottle](https://github.com/openstack/airship-in-a-bottle)
