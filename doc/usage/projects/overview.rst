Manage a project within makina-states - RFC
============================================

A bit of history, the first primitive layout
-------------------------------------------------
The initial layout was as follow::

    |- /srv/pillar/top.sls
    |- /srv/salt/top.sls
    |- /srv/salt/makina-projects/myproject -> /srv/projects/myproject/salt
    |- /srv/salt/makina-projects/myproject/top.sls -> /srv/projects/myproject/salt/top.sls
    |- /srv/pillar/makina-projects/myproject -> /srv/projects/myproject/pillar
    |- /srv/pillar/makina-projects/myproject/init.sls ->  /srv/projects/myproject/pillar/init.sls
    |- /srv/projects/myproject/salt (salt branch )
    |- /srv/projects/myproject/project (project branch)
    |- /srv/projects/myproject/pillar (pillar)
    |- /srv/projects/myproject/pillar/init.sls -> either a link to or a copy to regular file from /srv/projects/myproject/salt/PILLAR.sample.sls.

The different environment platforms
-------------------------------------
 We also want to distinguish at least those 3 environments

    :dev: The developper environments (laptop)
    :staging: the stagings and any other QA platform
    :prod:  the production platform

Objectives
------------
The layout and projects implementation  must allow us to

    - Automaticly rollback any unsucessful deployment
    - In production and staging, archive application content from N last deployments
    - In production and staging, archive the application data from N last deployments
    - In the near future, do warm/live migration
    - Make the development environment easily editable
    - Make the staging environment a production battletest server
    - Make the staging environment a production deliverables producer
    - Production can deploy from non complex builds, and the less possible dependant of external services

This way, we can manage and provision anything we need on those nodes, but we also separates security concerns.

In most cases building things on the production nodes is really a bad idea and error prone to lot of factors (network, build scripts bugs).
We handle this by providing a simili PAAS approach were we assemble artifacts to produce production ready deliverables.
Those artifacts will be able to run directly on production environments minus little provisionning, reonfiguration and upgrade paths
This is non so far from an **-extract-and-run-**.
For this, we inspired ouselves a lot from openshift_ and heroku_ (custom buildpacks) models.

Actual layout
-------------
Overview of the project source code repositories
+++++++++++++++++++++++++++++++++++++++++++++++++
A project woill have at least 2 repositories
- A repository where lives its sourcecode and deployment recipes

  This repository master branch consequently has the following structure::

    master
        |- what/ever/files/you/want
        |- .salt -> the salt deployment structure
        |- .salt/top.sls -> the salt sls file to execute to deploy the project

- A private repository with restricted access with any configuration data needed to deploy the
  application on the PAAS platform. This is in our case the project pillar tree::

     pillar master
        |- init.sls the pillar configuration

As anyways, you ll push changes to the PAAS platform, no matter what you push,
the PAAS platform will construct according to the pushed code :).

Overview of the paas directories
+++++++++++++++++++++++++++++++++
/srv/projects/myproject/git/project/
    Remote to push the project & salt branch to
/srv/projects/myproject/git/pillar
    Remote to push the project pillar branch to
/srv/projects/myproject/project/
    The local clone of the project branch
    From where we run in **editable** mode.
/srv/projects/myproject/pillar
    The project specific states pillar tree local clone
/srv/projects/myproject/data/
    Where must live any persistent data
/srv/projects/myproject/build/
    Directory in which we can build or deal with extra builds steps
    which need a temporary space to build on.
/srv/projects/myproject/run/
    Where the application runtimes files are.
    This is a separate directory in in **cooking** and **final** mode.
    But in **editable** mode, this directory is bind-mounted (a stronger symlink) to the **project** directory.
    In other words, the **project** directory will be the same as the **run** directory in **editable** mode.
    The application should always use the **run** directory to configure paths for configuration as even in **editable**
    mode the application **run** directory will be populated.
/srv/projects/myproject/deploy/current/ -> /srv/projects/myproject/deploy/<DATETIME>-<-UUID>/
    In **cooking** mode, all those files will be saved in the archives
    to be deployed in **final** mode (production).
/srv/projects/myproject/deploy/<DATETIME>-<ANOTHER-UUID>/
    A previous deployment
/srv/pillar/makina-projects/myproject -> /srv/projects/myproject/pillar
    pillar symlink
/srv/salt/makina-projects/myproject -> /srv/projects/myproject/salt/
    state tree project symlink

    * The **persistent configuration directories**

        /etc
             static global configuration (/etc)

    * The **persistent data directories**

        /var
            Global data directories (data & logs) (/var)

        /srv/projects/project/data

            * Specific application datas (/srv/projects/project/data)

                * Datafs and logs in zope world
                * drupal thumbnails
                * mongodb documentroot
                * ...

    * The **build working directory** where all build time procedure will operate before placing the results
      in the **run** directory.
    * The **run** directory is where is finally installed your application runtime files
      EG:

        * **django/python ala pip:** the virtualenv & root of runtime generated configuration files
        * **zope:** this will the root where the bin/instance will be lauched
        * **php webapps:** this will be your document root + all resources
        * **nodejs:** etc, this will be where nginx search for static files and
          where the nodejs app resides.

    * This separation will solve amongts all:

        * Mismatch in local sourcecode repositories between bare archive extraction and living
          filesystem on production environments.
        * Mismatch in runtimes files from one version to another

Networkly speaking, to enable switch of one container to another we have some solutions but in any case, no ports must be directly wired to the container.
**Never EVER**
Either:

    * Make the host receive the inbound traffic data and redirect (NAT) it to the underlying container
    * Make a proxy container receive all dedicated traffic and then this specific container will redirect the traffic to the real underlying production container.

For the big data containers, this will handled case per case by for exemple mounting the persistent volumes between both containers.

Project installation and operation modes
----------------------------------------
The editable mode
++++++++++++++++++
This mode will be mainly used in **development**.
In this mode, we will build and run the application directly from the repositories checkout to allow users to directly edit files in there and
having them available for testing without having to do a full redeploy dance.
The subtle thing to take into account is not to use directly the **project** directory for any hardcoded filesystem configuration but instead
the **run** directory.
Indeed, in this mode, the **run** directory is bind-mounted directly to the project directory.
This is to all the same paths references between dev and other environments.

The cooking mode
+++++++++++++++++
The **cooking** mode is a environment more suitable for **staging** environments.
The idea is there to add the cooking of production ready deliverables artifacts as a part of the build & deploy procedure.
In this mode, the application will be runned from the **run** directory but this one is not bind-mounted directly to the projet directory.
Indeed, the idea is here to configure and build for the runtime files as we were on production but we allow here to do heavy build steps.
As the **project** directory is there separated, you will certainly have to copy a large part of the project directory to the **run** directory.
This is normally already the case as you configured your application to run from this **run** directory but you ll certainly have to copy code
from the **project** directory to the **run** directory before building it.
At the end of the build steps, if it is sucessfull, we will synchronnise the **run** directory with the **deploy** directory.
After this synchonnisation we will make one or many **release deliverable archive** to be deployed later in production.
Those release archives will eventually be placed in the **releases** directory.

The final mode
+++++++++++++++
In production, we will mainly and mostly use the **final** mode.
In this mode, we do not run any complicated building states.
In other words we will totally skip the build macros.
Indeed, all the generated during build stuff which lands in the **run** directory should be saved in
previously baked archives in another environment (surely **staging**))
This mean that any dependency or configuration should be done before of after the build macro call.
In this mode the application is ran merely only from tarballs, and any hotfix to
something container in the **run** directory must be applied manually.
You can surely make a patch to be applied from the deliverables archives.
As notified briefly, in development and staging, it would be a
little awkward to rebuild the full deployment artifacts
because a one line editing in a CSS file.

In development mode
++++++++++++++++++++++
Installation / upgrade
~~~~~~~~~~~~~~~~~~~~~~
- We shutdown any service (normally not that much as we are on a fresh or a copy container)
- We setup any root or extra user ssh access to the underlying repository
- We checkout or sync the salt directory
- If the run directory in not already bind mounted to the **project** directory
    - we sync run with **project**
    - we wipe the **project** directory content
    - we bind-mount the **run** directory to the **project** directory in a persistent way
- We eventually build the project from **run**.
- We finally run upgrade steps if any

Notes:
Here, we wont do any extra copies between directories.
We also won't build any deployment artifacts.

In staging mode
+++++++++++++++++
Installation / upgrade
~~~~~~~~~~~~~~~~~~~~~~
- User pushes to pillar local repository and to salt local repository via mc_project push, this trigger the next steps via a hook
- We shutdown any service (normally not that much as we are on a fresh or a copy container)
- If size is low, we enlarge the container
- We do a partial or complete backup of the persistent data directory.
  Idea there is to allow for quick rollbacks in case of failed deployments.
- We execute the backup custom hook
  This is where the user can make happen a backup or dumps of global persistent data (mysql or pgsql datadirs)
- We wipe and recreate the **deploy** directory
- We archive (rsync) the **run** directory to the deployments archive folder
- We unpack the archives in the **deploy** directory
- We strictly sync the **deploy** directory to the **run** directory (rsync --delete)
- We start any service (normally not that much as we are on a fresh or a copy container)
- We finally run upgrade steps if any
- In case of a failure:

    - We shutdown any service
    - We move the failed **run** directory in the deployment archive folder
    - We sync back the previous deployment code to the **run** directory
    - We reload the old dumps
    - We resync the data directory from the old data directory.
    - We start any service (normally not that much as we are on a fresh or a copy container)

- We notify upstreamers of the project deployment status.
- Done.

In production mode
--------------------
- User pushes to pillar local repository and  to salt local repository via mc_project push, this trigger the next steps via a hook
- We pull the deployment archives from the staging environmenta if any
- We shutdown any service (normally not that much as we are on a fresh or a copy container)
- If size is low, we enlarge the container
- We do a partial or complete backup of the persistent data directory.
  Idea there is to allow for quick rollbacks in case of failed deployments.
- We execute the backup custom hook
  This is where the user can make happen a backup or dumps of global persistent data (mysql or pgsql datadirs)
- We archive (rsync) the **run** directory to the deployments archive folder
- We wipe and recreate the **deploy** directory
- We unpack the archives in the **deploy** directory
- We strictly sync the **deploy** directory to the **run** directory (rsync --delete)
- We start any service (normally not that much as we are on a fresh or a copy container)
- We finally run upgrade steps if any
- In case of a failure:

    - We shutdown any service (normally not that much as we are on a fresh or a copy container)
    - We move the failed **run** directory in the deployment archive folder
    - We sync back the previous deployment code to the **run** directory
    - We reload the old dumps
    - We resync the data directory from the old data directory.
    - We start any service (normally not that much as we are on a fresh or a copy container)

- We notify upstreamers of the project deployment status.
- Done.

Here, we wont do any extra copies between directories.
We also won't build any deployment artifacts.


IMPLEMENTATION: How a project is built and deployed
----------------------------------------------------
For now, at makinacorpus, we think this way:

    - Installing somewhere a mastersalt master controlling project nodes and only accessible by sysadmins
    - Installing elsewhere at least one project node which is:

        - linked to this mastersalt as a mastersalt minion
        - a salt minion linked to a salt master which is probably local
          and controlled by project members

Initialisation of a container environment
-----------------------------------------

   This will in order:

    - auth user
    - Create a new container on endpoint with those root credentials
    - Register DNS
      In a first time use a wildcarded DNS host on the specific endpoint target.
      Any additional dns setup (like client domain) will require some extra manual work to wire.
    - Create the layout
    - Generate root credentials and store them in grains on mastersalt
    - Configure the basic container pillar on mastersalt

        - root credentials
        - dns
        - firewall rules

    - Run the mastersalt container highstate.
    - Run the mastersalt container registration sls to wire the new container configuration (eg: firewall redirections)
    - Initiate the salt, pillar, and project git repositories inside the git folder
    - Clone local copies inside the project, pillar and salt directories
    - Send a mail to sysadmins and initial initer with the infos of the new platform access

        - basic http & https url access
        - ssh accces
        - root credentials

The nerve of the war: jinja macros and states, and execution modules
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Project states writing is done by layering a set of macros in a certain order.
Those macros will define and order salt states to deploy and amintain object from end to end.
The salt states and macros will bose abuse of execution modules to gather informations but also act on the underlying system.

Installation and upgrades deployment workflows
++++++++++++++++++++++++++++++++++++++++++++++++
The code is not pull by production server it will be pushed with git to the environment ssh endpoint:

    - Either by an automatted bot (jenkins)
    - By the user itself, hence he as enought access

In staging mode, before each build:
    - we shutdown all services
    - We move the **run** directory to an arcchive directory
    - We create a new and empty **run** directory

After each build where produced files are putted inside the **run** directory, we will launch/restart/upgrade the project from there.

The project common data structure
++++++++++++++++++++++++++++++++++
To factorize the code but also keep track of specific settings, those macros will use a common data mapping structure.
All those macros will take as input the **common** data structure which is a mapping containing all variables and metadata about your project.
This common data mapping is not copied over but passed always as a reference, this mean that you can change settings in a macro and see those changes in later macros.

The project common registry execution module helper
+++++++++++++++++++++++++++++++++++++++++++++++++++++
The base execution module used for project management is mc_project (:ref:`module_mc_project`).
This will define methods for:

- Crafting the base **common** data structure
- initialising the project filesystem layout, pillar and downloading the base sourcecode for deployment (salt branch)
- deploying and upgrading an already installed project.

The project macros interface
+++++++++++++++++++++++++++++
Each project must define a set of common macros which will be the interface of the project runner.

The macros in order of call:

        :gather_variables(common):
            This macro initialize the common macro with a possibly empty dict as entry.
            This will at a minimum update it via the mc_project.settings method.
            This will among all other thing set different variables from weither environment we are acting on.

            In **mixin** mode
                The path filesystem related variables will map the build and target directory to the project directory.

            In **final** mode
                The path filesystem related variables will map to the real **run** and **build** directory which ar
                e directly adjacant to the **project** directory according to project layout

        :pre_install(common):
            Macro to configure the project layout prior to anything.
            This is were the project layout will be initialized in term of filesystem speaking
            This code will just reject what the mc.project.init_project execution module function does.

            In **mixin** mode
                The **run** and **build** directory are createda but won't certainly be used.

            In **final** mode
                The **build** directory is wiped out and recreated.

        :configure(common):
            Configure a project before being able to build it.

            In **mixin** mode
                This will probably be a no-op as we won't do a separate build directory nor generate runtime artifacts.

            In **final** mode
                Common tasks here will be to download or copy build artifacts to the build directory

        :build(common):
            In **mixin** mode

            In **final** mode
                build project directly from the code repository code and deploy in this directory too (eg: /srv/projects/myproject/project

            Build a project using the build directory
                build project directly from the code repository code and deploy in this directory too (eg: /srv/projects/myproject/project

        :post_build(common):
            In **mixin** mode
                Build a project using the build directory

            In **final** mode
                D

        :bundle(common):
            In **mixin** mode
                N/A

            In **final** mode
                Construct arc

        :deploy(common):
            In **mixin** mode
                N/A

            In **final** mode

        :post_deploy(common):
            In **mixin** mode
                N/A
            In **final** mode
                The **run** directory

        :post_install(common):
            In **mixin** mode
                N/A

            In **final** mode

CLI Tools
---------

All of those commands will require you to be authenticated via a config file
-------------------------------------------------------------------------------------
~/.makinastates.conf:

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


Authenticated and distant call
- mkc listhosts
  List all available hosts to install projects onto
- mkc init_env <ENDPOINT> <platform_type>  [host] -> returns new platform UUID

  <platform_type>
    staging
    prod
    dev [MAY BE DEACTIVATED]
  <host>
    eventual host selection

  - create a container/vm to deploy our future project

- mkc init <ENDPOINT> <ENV_UUID> <project>

  Request for the creation of a project on a specific makina-states platform
  Returns by mail:

- mkc push <ENDPOINT> <UUID_ENV> <project>
    deploy our future project

    This will in turn:

        - push the pillar code
        - push the salt code triggering the local deploy hook

- mkc destroy <API_ENDPOINT> <UUID_ENV>

    Destroys and free any project resources on a located endpoint

- mkc destroy <API_ENDPOINT> <UUID_ENV> <project>

    Destroys and free any project resources on a located endpoint

- mkc trim <API_ENDPOINT> <UUID_ENV> <project> <size>

  Remove <size> from project storage disk usage.

- mkc enlarge <API_ENDPOINT> <UUID_ENV> <project> <size>

  Resize the project storage size with <size>

  For now size is not configurable and will be fixed at 5gb

API
----------
+---------------------------+-------------------------------+
|  host                     |   host_guests                 |
|      host(uuid)           |      host(uuid)               |
|      ip                   |      guest_type               |
|      port                 |      max                      |
|      ssh_user             |                               |
|      sudo                 |                               |
|      password             |                               |
|      guests_type          |                               |
+---------------------------+-------------------------------+
|  guest                    |   guest_type                  |
|      guest(uuid)          |       type                    |
|      label                |       label                   |
|      name                 |                               |
|      host(uuid)           |                               |
|                           |                               |
|  moved_guests             |                               |
|      old_host(uuid)       |                               |
|      new_host(uuid)       |                               |
|                           |                               |
|  guest_private_ips        |                               |
|      guestid              |                               |
|      private_ip           |                               |
|                           |                               |
|  guest_public_ips         |                               |
|      guestid              |                               |
|      public_ip            |                               |
|                           |                               |
|                           |                               |
.. _heroku: https://devce|-ter.heroku.com/articles/buildpack-api
.. _openshift: https://www.openshift.com/developers/deploying-and-building-applications
