.. _client_user_guide:

Shipyard Client User's Guide
============================

Shipyard provides three methods of interaction:
  #. An API - :ref:`shipyard_api`
  #. An API Client - api-client_
  #. A Command Line Interface (CLI) - :ref:`shipyard_cli`

Each of these components utilizes the prior.

::

   _________Client_________            __Server__
  |                        |          |          |
  | CLI -uses-> API Client | -calls-> |   API    |
  |________________________|          |__________|


This guide focuses on interaction with Shipyard via the CLI.

CLI Invocation Flow
-------------------

It is useful to understand the flow of a request made using the Shipyard CLI
first. There are several steps that occur with each invocation. This example
will demonstrate the flow of an invocation of the Shipyard CLI.

``Step 1: Invocation``::

  User --> CLI
  e.g.:
    $ shipyard get actions

As noted in CLI documentation, Shipyard handles authentication by leveraging
OpenStack's Keystone_ identity service. The CLI provides command line options
to specify credentials, or extracts them from the envrionment. For the example
started above, since the credentials are not specified, they would need to be
set in the envrionment prior to invocation. The credentials, regardless of
source, are passed from the CLI software to the API Client software.

``Step 2: API Client secures an authentication token``::

  API Client --> Keystone authentication
                           /
    (Auth Token) <---------

Shpipyard API Client calls Keystone to acquire an authentication token.

``Step 3: API Client discovers Shipyard``::

  API Client --> Keystone service discovery
                           /
    (Shipyard URL) <-------

Shipyard API Client calls Keystone to find the URL for the Shipyard API.

``Step 4: API Client invokes the appropriate Shipyard API``::

  API Client --> Shipyard API <--> Database, Airflow, etc...
                           /
    (JSON response) <------

As noted in the CLI documentation, some responses are YAML instead of JSON.

``Step 5: CLI formats response``::

  User <-- (Formatted Response) <-- CLI <-- (JSON response)
  e.g.:
    Name               Action                                   Lifecycle
    deploy_site        action/01BZZK07NF04XPC5F4SCTHNPKN        Failed
    update_site        action/01BZZKMW60DV2CJZ858QZ93HRS        Processing

The CLI maps the JSON response from the Shipyard API into a more tabular format
and presents it to the user.

Setup
-----

Server Components
~~~~~~~~~~~~~~~~~
Use of the Shipyard client requires that a working installation of the Shipyard
API is available. This may be accomplished by using the basic-ucp_ setup.
Detailed instructions are not part of this guide.

Local Environment
~~~~~~~~~~~~~~~~~
Several setup items may be required to allow for an operational Shipyard CLI,
including several work-arounds depending on how the Shipyard API is deployed.

Prerequisites:
  -  Python 3.5+
  -  git

.. note::

  It is recommended that a virtual environment setup with Python 3.5 is used to
  contain the dependencies and installation of the Shipyard client.

``Retrieve Shipyard client software from git``::

  git clone --depth=1 https://github.com/att-comdev/shipyard.git

``Install requirements``::

  cd shipyard
  pip install -r requirements.txt

``Build/install Shipyard``::

  python setup.py install

At this point, invoking shipyard as a command should result in a basic help
response::

  $ shipyard
  Usage: shipyard [OPTIONS] COMMAND [ARGS]...

    COMMAND: shipyard

    DESCRIPTION: The base shipyard command supports options that determine
    ...

``Setup environment variables``::

  export OS_USER_DOMAIN_NAME=default
  export OS_PROJECT_DOMAIN_NAME=default
  export OS_PROJECT_NAME=service
  export OS_USERNAME=shipyard
  export OS_PASSWORD=password
  export OS_AUTH_URL=http://keystone.ucp:80/v3

-  The values of these variables should match the credentials and endpoint of
   the target Shipyard API/Keystone environment.
-  The ``shipyard`` and ``password`` values are the insecure values used by
   default if not overridden by the installation of Shipyard.

``Configure hosts file, if necessary``::

  Add to /etc/hosts:

  10.96.0.44   keystone.ucp
  10.96.0.44   shipyard-api.ucp.svc.cluster.local

-  These values would need to be set in the case where DNS resolution of
   the Keystone and Shipyard URLs is not available.
-  The IP addresses should be set to resolve to the IP address of the ingress
   controller for the target Shipyard API/Keystone environment.
-  The value listed as ``keystone.ucp`` needs to match the value set for
   OS_AUTH_URL.
-  The value listed as ``shipyard-api.ucp.svc.cluster.local`` needs to match
   the value that Keystone returns when service lookup is done for the public
   URL for Shipyard.

Use Case: Ingest Site Design
----------------------------
Shipyard serves as the entrypoint for a deployment of the Undercloud Platform
(UCP). One can imagine the following activities representing part of the
lifecycle of a group of servers that the UCP would serve as the control plane:

Defintion
  A group of servers making up a ``site`` has been identified. Designs covering
  the hardware, network, and software are assembled.

Preparation
  The site is assembled, racking, and wiring is completed, and the hardware is
  readied for operation. The ``Genesis Node`` is preinstalled with an
  (Ubuntu 16.04) image. The Promenade_ genesis process similar to the
  basic-ucp_ process is configured on  and then run on the ``Genesis Node``.

  At this point, the UCP is ready for use. This is the when the Shipyard API
  is available for use.

Load Configuration Documents
  A user, deployment engineer, or automation -- i.e. the operator interacts
  with Shipyard, perhaps by using the CLI. The operator loads ``configdocs``
  which are a product of the definition step. These ``configdocs`` are
  declarative set of YAML documents using a format compatible with
  Deckhand_ and containing information usable by the other UCP components.

The interaction with Shipyard could happen as follows::

  $ git clone --depth=1 https://gitrepo.with.designs/site1.git

.. note::
  Assume: /home/user/site1 now contains .yaml files with Drydock_,
  Promenade_, Armada_, and Divingbell_ configurations, as well as
  secrets such as certificates, CAs, and passwords.

.. note::
  Assume: the appropriate credentials are set in the environment

::

  $ shipyard create configdocs site1 --directory=/home/user/site1
  Configuration documents added.
  Status: Validations succeeded
  Reason: Validation

This loads the documents as a named collection "site1" into Deckhand as a
bucket in a revision.

.. note::
  Alternatively, the command could have loaded a single file using
  --filename=<file>.yaml insetad of the --directory option

Following the creation of a configdocs collection in the Shipyard buffer, the
configdocs must be committed before Shipyard will use those documents as part
of an action::

  $ shipyard commit configdocs

During this command, the other UCP components are contacted to validate the
designs in Deckhand.  If the validations are not successful, Shipyard will not
mark the revision as committed.

.. important::
  It is not necessary to load all configuration documents in one step but each
  named collection may only exist as a complete set of documents (i.e. must be
  loaded together).

.. important::
  Shipyard will prevent the loading of two collections into the buffer at the
  same time unless --append is utilized. This option allows for the loading of
  multiple collections into the buffer to be later committed together.

  An example of this is a base collection that defines some common design
  elements, a secrets collection that contains certificates, and a
  site-specific collection that combines with the other two collections to
  fully define the site.


Use Case: Deploy Site
---------------------
Continuing the lifecycle steps from the Ingest Site Design use case, the
``operator`` proceeds with the deployment of the site.

Deployment
  The operator creates a deploy_site action and monitors its progress

Maintenance
  The operator loads new or changed configuration documents (as above),
  commits them, and creates an ``update_site`` action

The deployment interactions with Shipyard could happen as follows::

  $ shipyard create action deploy_site
  Name               Action                                   Lifecycle
  deploy_site        action/01BZZK07NF04XPC5F4SCTHNPKN        None

The deploy_site action is issued to Shipyard which relays a command to the
Airflow driven workflow processor. During and following execution of the
action, the operator can query the status and results of the action::

  $ shipyard get actions
  Name               Action                                   Lifecycle
  deploy_site        action/01BZZK07NF04XPC5F4SCTHNPKN        Processing

  $ shipyard describe action/01BZZK07NF04XPC5F4SCTHNPKN
  Name:                  deploy_site
  Action:                action/01BZZK07NF04XPC5F4SCTHNPKN
  Lifecycle:             Processing
  Parameters:            {}
  Datetime:              2017-11-27 20:34:24.610604+00:00
  Dag Status:            running
  Context Marker:        71d4112e-8b6d-44e8-9617-d9587231ffba
  User:                  shipyard

  Steps                                                              Index        State
  step/01BZZK07NF04XPC5F4SCTHNPKN/action_xcom                        1            success
  step/01BZZK07NF04XPC5F4SCTHNPKN/dag_concurrency_check              2            success
  ...

More information is returned than shown here - for sake of abbreviation. The
process of maintenance is very similar to the process of deploying a site.


.. _api-client: https://github.com/att-comdev/shipyard/tree/master/shipyard_client/api_client
.. _Armada: https://github.com/att-comdev/armada
.. _basic-ucp: https://github.com/att-comdev/ucp-integration/tree/master/manifests/basic_ucp
.. _Deckhand: http://deckhand.readthedocs.io/en/latest/
.. _Divingbell: https://github.com/att-comdev/divingbell
.. _Drydock: https://github.com/att-comdev/drydock
.. _Keystone: https://developer.openstack.org/api-ref/identity/index.html
.. _Promenade: https://github.com/att-comdev/promenade
