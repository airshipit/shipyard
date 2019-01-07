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

.. _shipyard_deployment_guide:

Deployment Guide
================

.. note::
  Shipyard is still under active development and this guide will evolve along
  the way

Deployment
----------

The current deployment makes use of the `airship-in-a-bottle`_ project to
set up the underlaying Kubernetes infrastructure, container networking
(Calico), disk provisioner (Ceph or NFS), and Airship components that are used
by Shipyard.

The `dev_minimal`_ manifest is the recommended manifest. Please see the
README.txt that exists in that manifest's directory.

This approach sets up an 'All-In-One' Airship environment that allows
developers to bring up Shipyard and the rest of the Airship components on a
single Ubuntu Virtual Machine.

The deployment is fully automated and can take a while to complete. It can take
30 minutes to an hour or more for a full deployment to complete.

Post Deployment
---------------

#. The environment should include the following after executing the required
   steps::

    # sudo kubectl get pods -n ucp | grep -v Completed
    NAME                                   READY     STATUS    RESTARTS   AGE
    airflow-scheduler-79754bfdd5-2wpxn     1/1       Running   0          4m
    airflow-web-7679866685-g99qm           1/1       Running   0          4m
    airflow-worker-0                       3/3       Running   0          4m
    airship-ucp-keystone-memcached-mem...  1/1       Running   0          31m
    airship-ucp-rabbitmq-rabbitmq-0        1/1       Running   0          35m
    armada-api-5488cbdb99-zjb8n            1/1       Running   0          12m
    barbican-api-5fc8f7d6f-s7h7j           1/1       Running   0          11m
    deckhand-api-7b476d6c46-qlvtm          1/1       Running   0          8m
    drydock-api-5f9fdc858d-lnxvj           1/1       Running   0          1m
    ingress-6cd5b89d5d-hzfzj               1/1       Running   0          35m
    ingress-error-pages-5c97bb46bb-zqqbx   1/1       Running   0          35m
    keystone-api-7657986b8c-6bf92          1/1       Running   0          31m
    maas-ingress-66447d7445-mgklj          2/2       Running   0          27m
    maas-ingress-errors-8686d56d98-vrjzg   1/1       Running   0          27m
    maas-rack-0                            1/1       Running   0          27m
    maas-region-0                          2/2       Running   0          27m
    mariadb-ingress-6c4f9c76f-lk9ff        1/1       Running   0          35m
    mariadb-ingress-6c4f9c76f-ns5kj        1/1       Running   0          35m
    mariadb-ingress-error-pages-5dd6fb...  1/1       Running   0          35m
    mariadb-server-0                       1/1       Running   0          35m
    postgresql-0                           1/1       Running   0          32m
    promenade-api-764b765d77-ffhv4         1/1       Running   0          7m
    shipyard-api-69888d9f68-8ljfk          1/1       Running   0          4m

.. _airship-in-a-bottle: https://git.airshipit.org/cgit/airship-in-a-bottle
.. _dev_minimal: https://git.airshipit.org/cgit/airship-in-a-bottle/tree/manifests/dev_minimal
