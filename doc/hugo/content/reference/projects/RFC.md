---
title: Projects RFC
tags: [reference, paas, projects]
weight: 40000
menu:
  main:
    parent: reference_projects
    identifier: reference_projects_rfc
---

RFC: corpus, embedded project configuration with salt
=====================================================
- <b>ORIGINAL 2012 DOCUMENT ACCUSING ITS AGE and converted to markdown</b>
- You'd better to read the [Original RST Document](https://github.com/makinacorpus/makina-states/blob/v2/doc/sphinx/v1/usage_projects/project_corpus.rst)

## The origin
Nowoday no one of the P/I/S/aaS existing platforms fit our needs and
habits. No matter of the gret quality of docker, heroku or openshift,
they did'nt make it for us. And, really, those software are great, they
inspired corpus a lot ! Please note also, that in the long run we
certainly and surely integrate those as plain **corpus** drivers to
install our projects on !

- For exemple, this is not a critisism at all, but that's why we were not
 enougth to choose one of those platforms (amongst all of the others):

    - [heroku](http://heroku.com/): non free
    - [docker](http://docker.io):
        -   Not enougth stable yet, networking integration is really a
            problem here. It is doable, but just complicated and out
            of scope.
        -   do not implement all of our needs, it is more tied to the
            'guest' part (see next paragraphs)
        -   But ! Will certainly replace the LXC guests driver in the
            near future.

    - [openshift](https://www.openshift.com/developers/deploying-and-building-applications)
    - Tied to SElinux and RedHat (we are more on the Debian front ;)).
      However, its great design inspired a lot of the corpus one.
    - [openstack](https://www.openstack.org/)
        - Irrelevant and not so incompatible for the PaaS platform, but
          again we didn't want locking, openstack would lock us in the first
          place. We want an agnostic PaaS Platform.

## The needs
That's why we created a set of tools to build the best flexible PaaS
platform ever. That's why we call that not a PaaS platform but a Glue
PaaS Platform :=).
-   Indeed, what we want is more of a CloudController + ToolBox +
    Dashboards + API.
-   This one will be in charge of making projects install any kind of
    compute nodes running any kind of VMs smoothly and flawlessly.
-   Those projects will never ever be installed directly on compute
    nodes but rather be isolated.
    -   They will be isolated primarly by isolation-level
        virtualisation systems (LXC, docker, VServer)
    -   Bue they must also be installable on plain VMs (KVM, Xen) or
        directly baremetal.

-   We don't want any PaaS platform to suffer from some sort of lockin.
-   We prefer a generic deployment solution that scale, and better
    AUTOSCALE !
-   All the glue making the configuration must be centralized and
    automatically orchestrated.
-   This solution must not be tied to a specific tenant (baremetal, EC2)
    nor a guest driver type (LXC, docker, XEN).
-   Corrolary, the **low level** daily tasks consists in managment of:
    -   network ( &lt; [OSI
        L3](http://en.wikipedia.org/wiki/OSI_model#Layer_3:_network_layer))
    -   DNS
    -   Mail
    -   operationnal supervision
    -   Security, IDS & Firewalling
    -   storage
    -   user management
    -   baremetal machines
    -   hybrid clouds
    -   public clouds
    -   VMs
    -   containers (vserver, LXC, docker)
    -   operationnal supervision

-   Eventually, on top of that orchestrate projects on that
    infrastructure
    -   installation
    -   continenous delivery
    -   intelligent test reports, deployment reports, statistic,
        delivery & supervision dashboards
    -   backups
    -   autoscale

Here is for now the pieces or technologies we use or are planning or
already using to achieve all of those goals:

-   Developer environments
    -   makina-corpus/vms + makina-corpus/makina-states + saltstack/salt
-   Bare metal machines provision
    -   makina-states + saltstack
    -   Ubuntu server
-   VMs (guests)
    -   Ubuntu based lxc-utils LXC containers + makina-states +
        saltstack
-   DNS:
    -   makina-states + bind: local cache dns servers & for the moment
        dns master for all zones
    -   **FUTURE** makina-states + powerdns: dynamic managment of all
        DNS zones
-   Filesystem Backup
    -   burp
-   Database backup
    -   [db\_smart\_backup](https://github.com/kiorky/db_smart_backup)
-   Network:
    -   ceph, openvswitch

-   Logs, stats:
    -   now: icinga2 / pnp for nagios
    -   future: icinga2 / logstash / kibana
-   Mail
    -   postfix

-   User managment (directory)
    -   Fusion directory + openldap
-   Security
    -   at least shorewall & fail2ban
-   CloudController
    -   saltstack
    -   makina-states + makina-states/mastersalt+ansible
-   projects installation, upgrades & contineous delivery
    -   makina-states (mc\_project, project\_creation)
-   autoscale
    -   makina-states

## The whole idea
- The basic parts of corpus PaaS platform:
    -   The cloud controller
    -   The cloud controller client applications
    -   The compute nodes
        -   Where are hosted guests
            -   Where projects run on
        -   The developer environments which are just a special kind of
            compute nodes

The first thing we will have is a classical makina-states installation
in mastersalt mode. We then will have salt cloud as a cloud controller
to control compute nodes via **makina-states.services.cloud.{lxc,
saltify, ...}** (lxc or saltify) Those compute nodes will install
guests. Those guests will eventually run the final projects pushed by
users.

- Hence an api and web interface to the controller we can:
    -   Add one or more ssh key to link to the host
    -   Request to link a new compute node
    -   Request to initialize a new compute node
    -   List compute nodes with their metadata (ip, dns, available slots,
        guest type)
    -   Get compute ndoos/container/vms base informations (ssh ip / port,
        username, pasword, dns names)
    -   Link more dns to the box
    -   Manage (add or free) the local storage.
    -   Destroy a container
    -   Unlink a compute node

The users will just have either: - Push the new code to deploy - Connect
via ssh to do extra manual stuff if any including a manual deployment

## Permission accesses
-   We will use an ldap server to perform authentication

## The different environment platforms
- We also want to distinguish at least those 3 environments, so 3 ways for
you to deploy at least.
    - dev: The developper environments (laptop)
    - staging: the stagings and any other QA platform
    - prod: the production platform

## Objectives
- The layout and projects implementation must allow us to
    -   Automaticly rollback any unsucessful deployment
    -   In production and staging, archive application content from N last
        deployments
    -   Make the development environment easily editable
    -   Make the staging environment a production battletest server
    -   Production can deploy from non complex builds, and the less possible
        dependant of external services
- For this, we inspired ouselves a lot from
    - [openshift](https://www.openshift.com/developers/deploying-and-building-applications)
    - and [heroku](https://devcenter.heroku.com/articles/buildpack-api)
      (custom buildpacks) models.

## Actual layout
### Overview of the project source code repositories
A project will have at least 2 local git repositories:

    /srv/projects/myproject/git/project.git/
      A repository where lives its sourcecode and deployment recipes
    /srv/projects/myproject/git/pillar.git/
      A repository where lives its pillar

This repository master branch consequently has the minimal following
structure:

    master
        |- what/ever/files/you/want
        |- .salt -> the salt deployment structure
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

-   A private repository with restricted access with any configuration
    data needed to deploy the application on the PAAS platform. This is
    in our case the project pillar tree:

        pillar master
           |- init.sls the pillar configuration

As anyways, you ll push changes to the PAAS platform, no matter what you
push, the PAAS platform will construct according to the pushed code :).
So you can even git push -f if you want to force things.

### Overview of the paas local directories

/srv/projects/myproject/project/

:   The local clone of the project branch from where we run in all
    modes. In other words, this is where the application runtimes files
    are. In application speaking

    -   **django/python ala pip:** the virtualenv & root of runtime
        generated configuration files
    -   **zope:** this will the root where the bin/instance will be
        lauched and where the buildout.cfg is
    -   **php webapps:** this will be your document root + all
        resources
    -   **nodejs:** etc, this will be where nginx search for static
        files and where the nodejs app resides.

/srv/projects/myproject/pillar

:   The project specific states pillar tree local clone.

/srv/projects/myproject/data/

:   Where must live any persistent data

/srv/pillar/makina-projects/myproject -&gt; /srv/projects/myproject/pillar

:   pillar symlink for salt integration

/srv/salt/makina-projects/myproject -&gt; /srv/projects/myproject/.salt/&lt;env&gt;

:   state tree project symlink for salt integration

/srv/salt/{\_modules,runners,outputters,states,pilalrs,renderers}/\*py -&gt; /srv/projects/myproject/.salt/&lt;typ&gt;/mod.py

:   custom salt python execution modules

The deployment procedure is as simple a running meta slses which in turn
call your project ones contained in a subfolder of the **.salt**
directory during the **install** phase.

The **.salt** directory will contain SLSs executed in lexicographical
order. You will have to take exemple on another projects inside
**makina-states/projects** or write your states. Those slses are in
charge to install your project.

-   The **persistent configuration directories**

    /etc

    :   static global configuration (/etc)

- the **persistent data directories**:<br/>
  If you want to deploy something inside, make a new archive in
  the release directory with a dump or a copy of one of
  those files/directories.

          /var

          :   Global data directories (data & logs) (/var) Minus the
              package manager cache related directories

          /srv/projects/project/data

          :   Specific application datas (/srv/projects/project/data)

              -   Datafs and logs in zope world
              -   drupal thumbnails
              -   mongodb documentroot
              -   ...

-   **Networkly speaking**, to enable switch of one container to another
    we have some solutions but in any case, **no ports** must be
    **directly** wired to the container. **Never EVER**.

Either:

-   Make the host receive the inbound traffic data and redirect (NAT) it
    to the underlying container
-   Make a proxy container receive all dedicated traffic and then this
    specific container will redirect the traffic to the real underlying
    production container.

## Procedures
- Those procedure will be implemented by either:
    -   Manual user operations or commands
    -   Git hooks
    -   salt execution modules
    -   jinja macros (collection of saltstack states)

All procedures are tied to a **default** sls inside the **.salt**
project folder and can per se be overriden.

### Project initialization/sync procedure
-   Initiate the project specific user
-   Initiate the ssh keys if any
-   Initiate the pillar and project bare git repositories inside the git
    folder
-   Clone local copies inside the project, pillar and salt directories
-   If the salt folder does not exists, create it
-   If any of default slses procedures are not yet present, create them
-   Wire the pillar configuration inside the pillar root
-   Wire the pillar init.sls file to the global pillar top file
-   Wire the salt configuration inside the salt root
-   Echo the git remotes to push the new deployement on.
-   Wire any salt modules in .salt/{\_modules,runners,etc}

### Project archive procedure
-   If size is low, we enlarge the container
-   run the pre archive hooks
-   archive the **project** directory in an **archive/deployed**
    subdirectory
-   run the post archive hooks (make extra dumps or persistent
    data copies)
-   run the archives rotation job

### Project Release-sync procedure
-   Be sure to sync the last git deploy hook from makina-states
-   Fetch the last commits inside the **deploy** directory

### Project install procedure
We run all slses in the project **.salt** directory which is not tied to
any default procedure.

### Project fixperms procedure

-   Set & **reset (enforce)** needed user accesses to the filesystem

### Rollback procedure

-   Only run if something have gone wrong
-   We move the failed **project** directory in the deployment
    **archives/&lt;UUID&gt;/project.failed** sub directory
-   We sync back the previous deployment code to the **project**
    directory
-   We execute the rollback hook (user can input database dumps reload)

##  Workflows

### Full procedure

-   project **deployment** is triggered
-   project **archive** procedure
-   project **initialization/sync** procedure
-   project **release-sync** procedure
-   project **fixperms** procedure
-   project **install** procedure
-   project **fixperms** procedure (yes again)
-   In error: **rollback** procedure

## IMPLEMENTATION: How a project is built and deployed
- For now, at makinacorpus, we think this way:
    -   Installing somewhere a mastersalt master controlling compute nodes
        and only accessible by **ops**.
    -   Installing elsewhere at least one compute node which will receive
        project nodes (containers):
        -   linked to this mastersalt as a mastersalt minion
        -   a salt minion linked to a salt master which is probably local
            and controlled by **project members aka devs**, by default
            these salt minion and salt master services are toggled off and
            the salt-call should be runned **masterless**
            (salt-call --local)

### Initialisation of a cloud controller
- Complex, contact [@makinacorpus](mailto:sysadmin@makina-corpus.com).
- This incude:
    -   Setting up the dns master & slaves for the cloud controlled zone.
    -   Setting up the cloud database
    -   Setting up at least one compute node to deploy projects
    -   Deploying vms

### Request of a compute node or a container
-   Edit the mastersalt database file to include your compute node and
    vms configuration.
-   Run any appropriate mastersalt runners to deploy & operate your
    compute nodes and vms

### Initialisation of a compute node
- This will in order:
    -   auth user
    -   check infos to attach a node via salt cloud
    -   Register DNS in the dns master for thie compute node and its related
        vms
    -   generate a new ssh key pair
    -   install the guest\_type base system
        (eg: makina-states.services.virt.lxc)
    -   Generate root credentials and store them in grains on mastersalt
    -   Configure the basic container pillar on mastersalt
        -   root credentials
        -   dns
        -   firewall rules
        -   defaultenv (dev, prod, preprod)
        -   compute mode override if any (default\_env
            inside /srv/salt/custom.sls)
    -   Run the mastersalt highstate.

### Initialisation of a project - container environment
This will in order:
-   auth user
-   Create a new container on endpoint with those root credentials
-   Create the layout
-   use the desired salt cloud driver to attach the distant host as a
    new minion
-   install the key pair to access the box as root
-   Generate root credentials and store them in grains on mastersalt
-   Configure the basic container pillar on mastersalt
    -   root credentials
    -   dns
    -   firewall rules
-   Run the mastersalt highstate

### Initialisation of a project

-   We run the initalization/sync project procedure
-   Send a mail to sysadmins, or a bot, and initial igniter with the
    infos of the new platform access
    -   basic http & https url access
    -   ssh accces
    -   root credentials
-   User create the project
-   Project directories are initialised

### upgrade of a project
- The code is not pull by production server it will be pushed with git to
  the environment ssh endpoint:
    -   Triggered either by an automatted bot (jenkins)
    -   By the user itself, hence he as enougth access
- In either way, the trigger is a git push.

### The nerve of the war: jinja macros and states, and execution modules

Project states writing is done by layering a set of saltstacl **sls**
files in a certain order. Those will ensure an automatic deployment from
end to end. The salt states and macros will abuse of execution modules
to gather informations but also act on the underlying system.

### The project common data structure

#### Overview
-   to factorize the configuration code but also keep track of specific
    settings, those macros will use a common data mapping structure
    which is good to store defaults but override in a common manner
    variables via pillar.
-   all those macros will take as input this **configuration** data
    structure which is a mapping containing all variables and metadata
    about your project.
-   this common data mapping is not copied over but passed always as a
    reference, this mean that you can change settings in a macro and see
    those changes in later macros.

### The project configuration registry execution module helper

The base execution module used for project management is
module\_mc\_project

It will call under the hood the latest **API** version of the
mc\_project module.

eg: `mc_project_2.*`

This will define methods for:

-   Crafting the base **configuration** data structure
-   initialising the project filesystem layout, pillar and downloading
    the base sourcecode for deployment (salt branch)
-   deploying and upgrading an already installed project.
-   Setting a project configuration

If there are too many changes in a project layout, obviously a new
project API module should be created and registered for the others to
keep stability.

### APIV2

#### The project execution module interface (APIV2)

Note that there two parts in the module:

-   One set of methods are the one you are most likely to use handle
    local deployment
-   One another set of methods is able to handle remote deployments over
    ssh. The only requirement for the other host is that makina-states
    should be installed first and ssh access should be configured
    previously to any deploy call. The requirement was to have only a
    basic ssh access, that why we did not go for a RAET or 0Mq salt
    deployment structure here.

See module\_mc\_project\_2

#### The project sls interface (APIV2)

Each project must define a set of common sls which will be the
interfaced and orchestred by the project execution module. Theses sls
follow the aforementionned procedures style.

**The important thing to now remember is that those special sls files
cannot be run without the project runner execution module**

Indeed, we inject in those sls contextes a special **cfg** variable
which is the project configuration and without we can't deploy
correctly.

-   We have two sets of sls to consider
    - The set of sls providen by a makina-states **installer**:<br/>
        this is specified at project creation and stored in
        configuration for further reference

    - The set of sls providen by the project itself in the .salt directory<br/>
        **this is where the user will customize it's deployment
        steps**.

The installer set is then included by default at the first generation of
the user installer set at the creation of the project.

## Project initialisation & installation
- Refer to project\_creation
- Some installers example: projects\_project\_list

