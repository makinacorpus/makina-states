
.. _project_corpus:

corpus, the Glue PaaS Platform -  RFC VERSION - 2
===================================================

The origin
------------
Nowoday no one of the P/I/S/aaS existing platforms fit our needs and habits.
No matter of the gret quality of docker, heroku or openshift, they did'nt make it for us.
And, really, those software are great, they inspired corpus a lot !
Please note also, that in the long run we certainly and surely integrate those
as plain **corpus** drivers to install our projects on !

For exemple, this is not a critisism at all, but that's why we were not enougth
to choose one of those platforms (amongst all of the others):

    `heroku`_

        non free

    `docker`_

        - Not enougth stable yet, networking integration is really a problem here.
          It is doable, but just complicated and out of scope.
        - do not implement all of our needs, it is more tied to the 'guest' part
          (see next paragraphs)
        - But ! Will certainly replace the LXC guests driver in the near future.

    `openshift`_
        Tied to SElinux and RedHat (we are more on the Debian front ;)).
        However, its great design inspired a lot of the corpus one.

    `openstack`_
        Irrelevant and not so incompatible for the PaaS platform, but again
        we didn't want locking, openstack would lock us in the first place.
        We want an agnostic PaaS Platform.

.. _openstack: https://www.openstack.org/
.. _docker:  http://docker.io
.. _heroku: http://heroku.com/
.. _dheroku: https://devcenter.heroku.com/articles/buildpack-api
.. _openshift: https://www.openshift.com/developers/deploying-and-building-applications

The needs
----------
That's why we created a set of tools to build the best flexible PaaS platform
ever. That's why we call that not a PaaS platform but a Glue PaaS Platform :=).

- Indeed, what we want is more of a CloudController + ToolBox + Dashboards +
  API.
- This one will be in charge of making projects install any kind of compute nodes
  running any kind of VMs smoothly and flawlessly.
- Those projects will never ever be installed directly on compute nodes but rather
  be isolated.

    - They will be isolated primarly by isolation-level virtualisation
      systems (LXC, docker, VServer)
    - Bue they must also be installable on plain VMs (KVM, Xen) or directly baremetal.

- We don't want any PaaS platform to suffer from some sort of lockin.
- We prefer a generic deployment solution that scale, and better AUTOSCALE !
- All the glue making the configuration must be centralized and automatically
  orchestrated.
- This solution must not be tied to a specific tenant (baremetal,
  EC2) nor a guest driver type (LXC, docker, XEN).
- Corrolary, the **low level** daily tasks consists in managment of:

    - network ( < `OSI L3 <http://en.wikipedia.org/wiki/OSI_model#Layer_3:_network_layer>`_)
    - DNS
    - Mail
    - operationnal supervision
    - Security, IDS & Firewalling
    - storage
    - user management
    - baremetal machines
    - hybrid clouds
    - public clouds
    - VMs
    - containers (vserver, LXC, docker)
    - operationnal supervision

- Eventually, on top of that  orchestrate projects on that infrastructure

    - installation
    - continenous delivery
    - intelligent test reports, deployment reports, statistic, delivery & supervision dashboards
    - backups
    - autoscale

Here is for now the pieces or technologies we use or are planning or already using to
achieve all of those goals:

- Developer environments

  - makina-corpus/vms + makina-corpus/makina-states + saltstack/salt

- Bare metal machines provision

  - makina-states + saltstack
  - Ubuntu server

- VMs (guests)

    - Ubuntu based lxc-utils LXC containers + makina-states + saltstack

- DNS:

    - makina-states + bind: local cache dns servers & for the moment dns master
      for all zones
    - **FUTURE** makina-states + powerdns: dynamic  managment of all DNS zones

- Filesystem Backup

    - burp

- Database backup

  - `db_smart_backup <https://github.com/kiorky/db_smart_backup>`_

- Network:

    - ceph, openvswitch

- Logs, stats:

    - now: icinga2 / pnp for nagios
    - future: icinga2 / logstash / kibana

- Mail

    - postfix

- User managment (directory)

    - Fusion directory + openldap

- Security

    - at least shorewall & fail2ban

- CloudController

    - saltstack
    - makina-states + makina-states/mastersalt

- projects installation, upgrades & contineous delivery

    - makina-states (mc_project, :ref:`project_creation`)

- autoscale

    - makina-states

The whole idea
----------------------
The basic parts of corpus PaaS platform:

    - The cloud controller
    - The cloud controller client applications
    - The compute nodes

        - Where are hosted guests

            - Where projects run on

        - The developer environments which are just a special kind of compute nodes


The first thing we will have is a classical makina-states installation in
mastersalt mode.
We then will have salt cloud as a cloud controller to control compute nodes
via **makina-states.services.cloud.{lxc, saltify, ...}** (lxc or saltify)
Those compute nodes will install guests.
Those guests will eventually run the final projects pushed by users.

Hence an api and web interface to the controller we can:

    - Add one or more ssh key to link to the host
    - Request to link a new compute node
    - Request to initialize a new compute node
    - List compute nodes with their metadata (ip, dns, available slots, guest type)
    - Get compute ndoos/container/vms base informations (ssh ip / port, username, pasword, dns names)
    - Link more dns to the box
    - Manage (add or free) the local storage.
    - Destroy a container
    - Unlink a compute node

The users will just have either:
- Push the new code to deploy
- Connect via ssh to do extra manual stuff if any including a manual deployment

Permission accesses
--------------------
- We will use an ldap server to perform authentication

The different environment platforms
-------------------------------------
We also want to distinguish at least those 3 environments, so 3 ways for you to
deploy at least.

:dev: The developper environments (laptop)
:staging: the stagings and any other QA platform
:prod:  the production platform

Objectives
------------
The layout and projects implementation must allow us to

- Automaticly rollback any unsucessful deployment
- In production and staging, archive application content from N last deployments
- Make the development environment easily editable
- Make the staging environment a production battletest server
- Production can deploy from non complex builds, and the less possible dependant of external services

For this, we inspired ouselves a lot from openshift_ and dheroku_ (custom buildpacks) models.

Actual layout
-------------
Overview of the project source code repositories
+++++++++++++++++++++++++++++++++++++++++++++++++
A project will have at least 2 local git repositories::

    /srv/projects/myproject/git/project.git/
      A repository where lives its sourcecode and deployment recipes
    /srv/projects/myproject/git/pillar.git/
      A repository where lives its pillar

This repository master branch consequently has the minimal following structure::

    master
        |- what/ever/files/you/want
        |- .salt -> the salt deployment structure
        |- .salt/notify.sls        -> notification code run at the end of the
        |                            deployment
        |- .salt/PILLAR.sample     -> default pillar used in the project, this
        |                             file will be loaded inside your
        |                             configuration
        |- .salt/rollback.sls      -> rollback code run in case of problems
        |- .salt/archive.sls       -> pre save code which is run upon a deploy
        |                             trigger
        |- .salt/fixperms.sls      -> reset permissions script run at the end of
        |                            deployment
        |- .salt/_modules          -> custom salt modules to add to local salt
        |       /_runners             install
        |       /_outputters
        |       /_states
        |       /_pillars
        |       /_renderers
        |
        |- .salt/00_DEPLOYMENT.sls -> all other slses will be executed in order
                                      and are to be provided by th users.

- A private repository with restricted access with any configuration data needed to deploy the
  application on the PAAS platform. This is in our case the project pillar tree::

    pillar master
       |- init.sls the pillar configuration

As anyways, you ll push changes to the PAAS platform, no matter what you push,
the PAAS platform will construct according to the pushed code :).
So you can even git push -f if you want to force things.

Overview of the paas local directories
+++++++++++++++++++++++++++++++++++++++
/srv/projects/myproject/project/
    The local clone of the project branch from where we run in all modes.
    In other words, this is where the application runtimes files are.
    In application speaking

        * **django/python ala pip:** the virtualenv & root of runtime generated configuration files
        * **zope:** this will the root where the bin/instance will be lauched
          and where the buildout.cfg is
        * **php webapps:** this will be your document root + all resources
        * **nodejs:** etc, this will be where nginx search for static files and
          where the nodejs app resides.


/srv/projects/myproject/pillar
    The project specific states pillar tree local clone.

/srv/projects/myproject/data/
    Where must live any persistent data

/srv/pillar/makina-projects/myproject -> /srv/projects/myproject/pillar
    pillar symlink for salt integration
/srv/salt/makina-projects/myproject -> /srv/projects/myproject/.salt/<env>
    state tree project symlink for salt integration
/srv/salt/{_modules,runners,outputters,states,pilalrs,renderers}/\*py -> /srv/projects/myproject/.salt/<typ>/mod.py
    custom salt python execution modules

The deployment procedure is as simple a running meta slses which in turn
call your project ones contained in a subfolder of the **.salt** directory
during the **install** phase.

The **.salt** directory will contain SLSs executed in lexicographical order.
You will have to take exemple on another projects inside **makina-states/projects**
or write your states.  Those slses are in charge to install your project.

* The **persistent configuration directories**

    /etc
         static global configuration (/etc)

* The **persistent data directories**
    If you want to deploy something inside, make a new archive in the release
    directory with a dump or a copy of one of those files/directories.

    /var
        Global data directories (data & logs) (/var)
        Minus the package manager cache related directories

    /srv/projects/project/data

        * Specific application datas (/srv/projects/project/data)

            * Datafs and logs in zope world
            * drupal thumbnails
            * mongodb documentroot
            * ...

* **Networkly speaking**, to enable switch of one container to another
  we have some solutions but in any case, **no ports** must be
  **directly** wired to the container. **Never EVER**.

Either:

* Make the host receive the inbound traffic data and redirect (NAT) it to the underlying container
* Make a proxy container receive all dedicated traffic and then this specific container will redirect the traffic to the real underlying production container.

Procedures
-------------
Those procedure will be implemented by either:

    - Manual user operations or commands
    - Git hooks
    - salt execution modules
    - jinja macros (collection of saltstack states)

All procedures are tied to a **default** sls inside the **.salt** project
folder and can per se be overriden.

Project initialization/sync procedure
+++++++++++++++++++++++++++++++++++++
- Initiate the project specific user
- Initiate the ssh keys if any
- Initiate the pillar and project bare git repositories inside the git folder
- Clone local copies inside the project, pillar and salt directories
- If the salt folder does not exists, create it
- If any of default slses procedures are not yet present, create them
- If we are in editable mode, clone from origin remote
- Wire the pillar configuration inside the pillar root
- Wire the pillar init.sls file to the global pillar top file
- Wire the salt configuration inside the salt root
- Echo the git remotes to push the new deployement on.

Project archive procedure
++++++++++++++++++++++++++
- If size is low, we enlarge the container
- run the pre archive hooks
- archive the **project** directory in an **archive/deployed** subdirectory
- run the post archive hooks (make extra dumps or persistent data copies)
- run the archives rotation job

Project Release-sync procedure
++++++++++++++++++++++++++++++
- Be sure to sync the last git deploy hook from makina-states
- Fetch the last commits inside the **deploy** directory

Project install procedure
++++++++++++++++++++++++++
We run all slses in the project **.salt** directory which is not tied to any
default procedure.

Project fixperms  procedure
++++++++++++++++++++++++++++
- Set & **reset** needed user accesses to the filesystem

Project notification procedure
+++++++++++++++++++++++++++++++
- We  echo by default on the stdout the status of the deployment but it can be
  overidden by editing the **notify.sls** file.

Rollback procedure
+++++++++++++++++++++
- Only run if something have gone wrong
- We move the failed **project** directory in the deployment
  **archives/<UUID>/project.failed** sub directory
- We sync back the previous deployment code to the **project** directory
- We execute the rollback hook (user can input database dumps reload)

Workflows
---------
Full procedure
+++++++++++++++++
- project deployment trigger procedure
- project archive procedure
- project initialization/sync procedure
- project release-sync procedure
- project install procedure
- In error: rollback procedure
- In any cases (error, success):  project notification procedure

IMPLEMENTATION: How a project is built and deployed
----------------------------------------------------
For now, at makinacorpus, we think this way:

- Installing somewhere a mastersalt master controlling compute nodes and only accessible by **ops**.
- Installing elsewhere at least one compute node which will receive project
  nodes (containers):

    - linked to this mastersalt as a mastersalt minion
    - a salt minion linked to a salt master which is probably local
      and controlled by **project members aka devs**

Initialisation of a cloud controller
-----------------------------------------
Complex, contact @makinacorpus

This incude
- Setting up the dns master for the cloud controlled zone.
- Setting up the cloud database
- Setting up a basic pillar and mastersalt setup to finnish the box install
- Configuring up mastersalt to use pgsql extpillar
- Configuring up corpus.reactor and corpus.web on top of mastersalt

Request of a compute node or a container
------------------------------------------
- Edit the mastersalt database file to include your compute node and vms
  configuration.
- Run any appropriate mastersalt **mc_cloud_XX** runners to deploy your compute
  nodes and vms

Initialisation of a compute node
--------------------------------
This will in order:

- auth user
- check infos to attach a node via salt cloud
- Register DNS in the dns master for thie compute node and its related vms
- generate a new ssh key pair
- install the guest_type base system (eg: makina-states.services.virt.lxc)
- Generate root credentials and store them in grains on mastersalt
- Configure the basic container pillar on mastersalt

    - root credentials
    - dns
    - firewall rules
    - defaultenv (dev, prod, preprod)
    - compute mode override if any (default_env inside /srv/salt/custom.sls)

- Run the mastersalt highstate.

Initialisation of a container environment
-----------------------------------------
This will in order:

- auth user
- Create a new container on endpoint with those root credentials
- Create the layout
- use the desired salt cloud driver to attach the distant host as a new minion
- install the key pair to access the box as root
- Generate root credentials and store them in grains on mastersalt
- Configure the basic container pillar on mastersalt

    - root credentials
    - dns
    - firewall rules

- Run the mastersalt container highstate.

Initialisation of a project
++++++++++++++++++++++++++++++++++++++
- We run the initalization/sync project procedure
- Send a mail to sysadmins, or a  bot, and initial igniter with the infos of the new platform access

    - basic http & https url access
    - ssh accces
    - root credentials

- User create the project
- Project directories are initialised
- User receive an email with the git url to push on

upgrade  of a project
+++++++++++++++++++++
The code is not pull by production server it will be pushed with git to the environment ssh endpoint:

- Triggered either by an automatted bot (jenkins)
- By the user itself, hence he as enought access

In either way, the trigger is a git push.


The nerve of the war: jinja macros and states, and execution modules
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Project states writing is done by layering a set of macros in a certain order.
Those macros will define and order salt states to deploy and amintain object from end to end.
The salt states and macros will bose abuse of execution modules to gather informations but also act on the underlying system.

The project common data structure
++++++++++++++++++++++++++++++++++
Overview
^^^^^^^^
- to factorize the configuration code but also keep track of specific settings, those macros will use a common data mapping structure
  which is good to store defaults but override in a common manner variables via
  pillar.
- all those macros will take as input this **configuration** data structure which is a mapping containing all variables and metadata about your project.
- this common data mapping is not copied over but passed always as a reference, this mean that you can change settings in a macro and see those changes in later macros.

Local configuration state
^^^^^^^^^^^^^^^^^^^^^^^^^^
As a project can stay in production for a while without be redeployed, we need
to gather static informations on how he got deploymed.
The previous quoted mapping should be partially and enoughtly saved to know
enought of local installation not to break it.

The project state must save:
    - all configuration variables
    - the project api_version

This must be done:

    - After a sucessful deployment
    - After a sucessful initialization
    - By calling the set_configuration method with one or more specified
      arguments in the form parameters=value

The project configuration registry execution module helper
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
The base execution module used for project management is mc_project module + all
api specific mc_project_APIN modules.
This will define methods for:

- Crafting the base **configuration** data structure
- initialising the project filesystem layout, pillar and downloading the base sourcecode for deployment (salt branch)
- deploying and upgrading an already installed project.
- Setting a project configuration

This module should know then how to redirect to the desired API specific
mc_project module (eg: mc_project_2 for the project APIV2)

If there are too many changes in a project layout, obviously a new project API
module should be created and registered for the others to keep stability.

APIV2
++++++
The project execution module interface (APIV2)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**name** is the project name.

mc_project.init_project(name, \*\*kwargs)
    initialise the local project layout and configuration.
    any kwarg will override its counterpart in default project configuration

mc_project.deploy_project(name, only=None)
    (re)play entirely the project deployment while maybe limiting to a/some specific
    step(s)

mc_project.get_configuration(name)
    get the local project configuration mapping

mc_project.set_configuration(name, cfg=None, \*\*kwargs)
    save a total configuration or particular configuration paramaters locally

mc_project.archive(name, \*args, \*\*kwargs)
    do the archive procedure

mc_project.sync_hooks(name, \*args, \*\*kwargs)
    regenerate git hooks

mc_project.sync_modules(name, \*args, \*\*kwargs)
    deploy salt modules inside .salt

mc_project.release_sync(name, \*args, \*\*kwargs)
    do the release-sync procedure

mc_project.install(name, \*args, \*\*kwargs)
    do the install procedure

mc_project.notify(name, \*args, \*\*kwargs)
    do the notifiation procedure

mc_project.rollback(name, \*args, \*\*kwargs)
    do the rollback procedure

The project sls interface (APIV2)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Each project must define a set of common sls which will be the interfaced and
orchestred by the project execution module.
Theses sls follow the aforementionned procedures style.

**The important thing to now remember  is that those special sls files cannot be run
without the project runner execution module**

Indeed, we inject in those sls contextes a special **cfg** variable which is the
project configuration and without we can't deploy correctly.

- We have two sets of sls to consider

    - The set of sls providen by a makina-states **installer**
        this is specified at project creation and stored in configuration for further reference
    - The set of sls providen by the project itself in the .salt directory
        **this is where the user will customize it's deployment steps**.

The installer set is then included by default at the first generation of the
user installer set at the creation of the project.

EG: in .salt/notify.sls we will have something that looks to::

    include:
      - makina-states.projects.2.generic.notify

- Some installers example:
    - generic
      base sls used by all other macros
    - `tilestream <https://github.com/makinacorpus/tilestream-salt>`_

Project initialisation
-----------------------
You will need in prerequisites:

    - 2 git repositories to contain your project and your pillar
    - A development VM based on makina-corpus/vms

A new project initialisation on a developpment box can be done as follow::

    salt-call -lall mc_project.init_project <NAME>

When the project is initialized, you can pull locally the 2 given remotes.
If you missed them, you can retrieve them in the configuration::

    salt-call -lall mc_project.get_configuration <NAME>

You can then push your changes to your preferred central repository (company, github)

Project installation
-----------------------
Once the project is initialized, you can deploy it by issuing
a git push to the development or production environment, this will
run the full deployment procedure

But, if you are testing your stuff or want to run it manually, just
log on your environment and issue::

    salt-call -lall mc_project.deploy <NAME> only=install,fixperms

Indeed, this will only run the sub steps which install the project and not
the overhead of the archive+release_sync+rollback+notify procedure.


corpus CLI Tools (not implemented yet)
-----------------------------------------------------
All of those commands will require you to be authenticated via a config file::

    ~/.makinastates.conf

This is a yaml configuration file::

    envnickname:
        url: <ENDPOINTURL>
        id: <dientifier
        password <password>

EG:

     prod:
        url: masteralt.foo.net
        id: someone@foo.net
        password s3cr3t
     dev:
        url: devhost.local
        id: someone@foo.net
        password s3cr3t3

Commands
+++++++++

Authenticated and distant call

- corpus computenode_list

List all available hosts to install projects onto

- corpus computenode_init <ENDPOINT> <platform_type>  [host] -> returns new platform UUID

<platform_type>
staging
prod
dev [MAY BE DEACTIVATED]
<host>
eventual host selection

create a container/vm to deploy our future project

- corpus computenode_switchmode <ENDPOINT> <ENV_UUID> <operation_mode>

Request for the sitch of an operation mode to another

- corpus computenode_init <ENDPOINT> <platform_type> [host] [space separted list of guest types]-> returns new platform UUID

<platform_type>
staging
prod
dev [MAY BE DEACTIVATED]
<host>
eventual host selection

request for the link of an host for container/vm to deploy our futures guests

- corpus computenode_infos <ENDPOINT> <ENV_UUID>

List for a specific compute node tenant

        - available guest slots
        - a list of slots with the number at a minium and hence we have access
          the guests metadatas

- corpus project_create <API_ENDPOINT> project <- return uuid

    Create a new project to link containers onto

- corpus guest_create <API_ENDPOINT> guest <- return guest_id

    Create a new guest to push project code onto

- corpus push <ENDPOINT> <guest_id> <project>
    deploy our future project

    This will in turn:

        - push the pillar code
        - push the salt code triggering the local deploy hook

- corpus guest_delete <API_ENDPOINT> <guest_id>

  Delete a guest

- corpus project_destroy <API_ENDPOINT> <UUID_ENV> <project>

  Destroys and free any project resources on a located endpoint

- corpus trim <API_ENDPOINT> <UUID_ENV> <guest> <size>

  Remove <size> from project storage disk usage.

- corpus enlarge <API_ENDPOINT> <UUID_ENV> <guest> <size>

  Resize the project storage size with <size>

For now size is not configurable and will be fixed at 5gb


