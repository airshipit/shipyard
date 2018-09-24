========
Shipyard
========

Shipyard adopts the Falcon web framework and uses Apache Airflow as the backend
engine to programmatically author, schedule and monitor workflows.

Find more documentation for Shipyard on
`Read the Docs <https://airship-shipyard.readthedocs.io/>`_.

The current workflow is as follows:

1. Initial region/site data will be passed to Shipyard from either a human
   operator or Jenkins
2. The data (in YAML format) will be sent to `Deckhand`_ for validation and
   storage
3. Shipyard will make use of the post-processed data from DeckHand to interact
   with `Drydock`_.
4. Drydock will interact with `Promenade`_ to provision and deploy bare metal
   nodes using Ubuntu MAAS and a resilient Kubernetes cluster will be created
   at the end of the process
5. Once the Kubernetes clusters are up and validated to be working properly,
   Shipyard will interact with `Armada`_ to deploy OpenStack using
   `OpenStack Helm`_
6. Once the OpenStack cluster is deployed, Shipyard will trigger a workflow to
   perform basic sanity health checks on the cluster

Note: This project, along with the tools used within are community-based and
open sourced.

Mission
-------

The goal for Shipyard is to provide a customizable *framework* for operators
and developers alike. This framework will enable end-users to orchestrate and
deploy a fully functional container-based Cloud.

Getting Started
---------------

This project is under development at the moment. We encourage anyone who is
interested in Shipyard to review our `documentation`_.

Bugs
----

If you find a bug, please feel free to create a `Storyboard issue`_.

.. _Deckhand: https://github.com/openstack/airship-deckhand
.. _Drydock: https://github.com/openstack/airship-drydock
.. _Promenade: https://github.com/openstack/airship-promenade
.. _Armada: https://github.com/openstack/airship-armada
.. _OpenStack Helm: https://github.com/openstack/openstack-helm
.. _documentation: https://airship-shipyard.readthedocs.io/
.. _Storyboard issue: https://storyboard.openstack.org/#!/project/1010
