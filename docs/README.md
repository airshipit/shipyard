## Shipyard ##

Shipyard adopts the Falcon web framework and uses Apache Airflow as backend engine to programmatically
author, schedule and monitor workflows. 

The current workflow is as follows:

1. Inital region/site data will be passed to Shipyard from either a human operator or Jenkins
2. The data (in YAML format) will be sent to [DeckHand](https://github.com/att-comdev/deckhand) for processing
3. Shipyard will make use of the post-processed data from DeckHand to interact with [DryDock](https://github.com/att-comdev/drydock)
4. DryDock will interact with [Promenade](https://github.com/att-comdev/promenade) to provision and deploy
   bare metal nodes using Ubuntu MAAS and Promenade will create a resilient Kubernetes cluster.
5. Once the Kubernetes clusters are up and validated to be working properly, Shipyard will interact with
   [Armada](https://github.com/att-comdev/armada) to deploy OpenStack using [OpenStack Helm](https://github.com/openstack/openstack-helm) 
6. Once the OpenStack cluster is deployed, Shipyard will trigger a workflow to perform basic sanity health
   checks on the cluster


Note: This project, along with the tools used within are community-based and open sourced.


### Mission ###

The goal for Shipyard is to provide a customizable *framework* for operators and developers alike.  This 
framework will enable end-users to orchestrate and deploy a fully functional container-based Cloud


### Roadmap ###

The detailed Roadmap can be viewed on the [LCOO JIRA](https://openstack-lcoo.atlassian.net/projects/SHIPYARD/issues/)

- Create Helm Charts for Airflow
- Create Helm Charts for Shipyard
- Create Falcon API Framework
- Integrate with DeckHand, DryDock/Promenade, Armada


### Getting Started ###

This project is under development at the moment.  We encourage anyone who is interested in Shipyard to review
our [Installation](https://github.com/att-comdev/shipyard/tree/master/docs) documentation


### Bugs ###

Bugs are traced in [LCOO JIRA](https://openstack-lcoo.atlassian.net/projects/SHIPYARD/issues/).  If you find 
a bug, please feel free to create a GitHub issue and it will be synced to JIRA.

