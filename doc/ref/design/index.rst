Design
========

Main states kind segregation
-----------------------------
In makina states we have organised our states in the following way:

    :controllers: states related to the base salt infrastructure (layout, deamons, permissions)
    :nodetypes: states related only to the hardware, the machine type  or virtualisation facillity
    :localsettings: states related to the base machine configuration minus all that can looks like a service or a deamon (eg: directories creations, hosts managment, pam, vim but not ssh)
    :services: states related to services configuration (eg: ssh, docker, apache, backups scripts & crons)
    :projects: Set of macros to be externallly included project consumers as the base to setup their projects using makina-states bricks

For all those kinds, we have execution modules, sub-execution modules and formulaes containers. to leverage and factorize all variables and have well placed macros.

For exemple, php users will certainly have to deal the following files:

    - :mc_states/modules/services.py: registries
    - :mc_states/services/{http,php}/*.sls: states files (formulaes)
    - :/srv/pillar/foo.sls: custom settings

Wrap-up
~~~~~~~
Tree of different configuration flavors inheritance::

    Controllers +--> salt-minion <------------------+
       |        |                                   |
       |        +--> salt-master --controlling------+
       |        |
       |        +--> mastersalt-minion <------------+
       |        |                                   |
       |        +--> mastersalt-master -controlling-+
    controllers                                     _________________
    controlling             NODETYPES - INHERITANCE                  |
     nodetypes             |       server                            |
       |                   |         |                               |
    ---+ ------+           |         +->vm                           |
     NODETYPE  |- - - - - -|         |   |                           |
    ---+-------+           |         |   +--> lxccontainer           |
       |                   |         |   |                           |
       |                   |         |   +--> dockercontainer        |
    configuration          |         |                               |
    installed on           |         +->devhost                      |
     a nodetype            |             |                           |
       |                   |             +->vagrantvm                |
       |                   |_________________________________________|
       |
    ---+-----------+
      server:base  |
     configuration |
    --+--------+---+
      |        |
      |        |            +---------------+
      |        |            |               |  solr
      |     running on <----+ Service:base  |   |
      |                     |               |   |      docker
    LOCALSETTINGS           +-+-------------+  tomcat   |
    =============             |                 |       |
    ldap, nscd, profile     service tree        |      lxc
    vim git sudo localrc      |                java     |
    pkgs pkgmgr shell         |   bacula        |       |
    user (...)                |    |            |     virt
                              |    |   ntp      |       |
       _______________________|____|____|_______|_______|_
        | |    |   |     |       | |  |                   \
        | ldap | salt/mastersalt | |  |    .-- nginx      |
        |  |   |                 | |  |   /__ apache      |
        | nscd |                ssh|  http               php____ phpfpm
        |      |                   |                         |
        |      |                   |                         modphp
        db   mail                  |
        /\     \                   shorewall
       /  \     \____ postfix
    pgsql  mysql \
                  \__ dovecot




Hooks
~~~~~
Hooks in the makina-states meaning have two functions:

    - Provide a robust orchestration mecanism
    - Provide a way to skip a full subset of states by non inclusion of the real states files during different execution modes (standalone, full).

Those hooks are just states which use the **mc_proxy.hook** function wich does nothing more forward the changes of acendant of the states to the descendant of this state.
For example in::

    one:
        cmd.run:
            - name: /bin/true

    foo:
        mc_hook.proxy:
            - require:
                - cmd: one

    two
        mc_hook.proxy:
            - require:
                - mc_proxy: foo

As one will return a change, foo will also trigger in turn a change, thus two will see foo as 'changed'.

You can also easily skip a full subset of states, imagining the three following files:

- **a.sls**::

    include:
        - hooks

    one:
        cmd.run:
            - name: /bin/true
            - watch_in
                - cmd: one

- **hooks.sls**::

     foo:
        mc_hook.proxy: []


- **c.sls**::

    include:
        - hooks
        {{ if something }}
        - a
        {{ endif }}

    two
        mc_hook.proxy:
            - require:
                - mc_proxy: foo

You just discoved the magic of hooks to make custom execution modes without having to clutter your states files with custom require/includes, you just have to subscribe to isolated hooks, and in the real states files, to also subscribe to those hooks. In the listeners, you just have to conditonnaly include the real state file for the job to be correctly executed with the other states.

Execution modes
~~~~~~~~~~~~~~~~~
As we now extensivly use auto inclusion, we are particularly exposed to the **state bloat megalomania** when including a small little state will make rebuild the most part of makina-states. To prevent this, there are 2 main modes of execution and when the full mode will configure from end to end your machine, the standalone mode will skip most of the included states but also some of your currently called sls file.

The main use case is that the first time, you need to install a project and do a lot of stuff, but on the other runs, you just need to pull your new changesets and reload apache.
The full mode is the standart mode, and the **light** mode is called **standalone**.
That's why you ll see most formulaes declined in two sls flavors.

By convention, in those formulaes, we make the **standalone** one as a macro taking at least a **full** boolean parameter and then call it at the end with **full=false**. Then we write the normal sls calling this same little macro with **full=true**.

It is then up to the user of in the other sls includes to choose which sls to apply for the specific use case.

For example:

- services/awesome/mysuperservice-standalone.sls::

    {% macro do(full=True) %}

- services/awesome/mysuperservice.sls::


By hand, i will do the first time:


    samt

To configure a machine via makina-states, we use registries which will feed their exposed variables through different configuration sources where the main ones are the grains and the pillar.

  - Set tags in pillar or grains or configuration
  - Include directly a specific state

As soon as those tags are run, they will set a grain on the machine
having the side effect to register that part of our states to be 'auto installed'
in the future highstates, they will even run even if we have not included them explicitly.

TODO:
  - We are planning the uninstall part but it is not yet done
  - In the meantime, to uninstall a state, you ll have first to remove the grain/pillar/inclusion
    Then rerun the highstate and then code a specific cleanup sls file if you want to cleanup
    what is left on the server

As you certainly have understood, this is to enable some kind of local auto configuration
based on previous runs and on configuration (grains + states inclusions + pillar).
All this configuration is stored in macros used by all the states, look at ./_macros.

To sum up, we have made all of those states reacting and setting tags for the system
to be totally dynamic. All the things you need to do is to set in pillar or in grains
the appropriate values for your machine to be configured.

In other words, you have 4 levels to make salt install you a 'makina state'
which will be automaticaly included in the next highstate:

  - Direct inclusion via the 'include:' statement:
      - include makina-states.services.http.apache
  - Install directly the state via a salt/salt-call state.sls
      - salt-call state.sls makina-states.services.http.apache
  - Appropriate grain configuration slug
      - salt-call --local grains.setval makina-states.services.http.apache true
  - Appropriate pillar configuration slug
      - makina-states.services.http.apache: true in a pillar file
  - Run the highstate, and as your machine is taggued, apache
    will be installed

You can imagine that there a a lot of variables that can modify the configurationa applied to a minion.
To find what to do, we invite you to just read the states that seem to be relevant to your needs.
You can also have a look to _macros/*.jinja files.

As grains are particulary insecures, pay attention that states chained
by this inheritance are only limited to the base installation
and do not expose too much sensitive data coming from associated pillars

To better understand how things are done, this is an non exhaustive graph
or our states tree:


You may have already note that there are some main kind of tags
  - server nodetypes: which server do I run on?
  - 2 kinds of salt controllers (salt/mastersalt)
      * salt is a local project salt master
      * mastersalt is the salt master of the admin guys
  - services

Some rules to write makina-states states:
  - Learn and use the [Kind]register mecanism. (its a one liner saving your ass)
  - Never ever write an absolute path, use localsettings.locations.PATH_PREFIX
  - If your path is not in that mapping and is enoughtly generic, just add it.
  - Never ever use short form of states (states without names, use states unique IDs)
  - Please use as much as possible require(_in)/watch(_in) to ensure your configuration
    slugs will be correctly scheduled
  - Use CamelCase for variables names for them to not been marked as jinja private variables
  - On the contrary, use _underscore_case for very private macros variables




.. toctree::
   :maxdepth: 2

    registries
    formulaes
    macros
    hooks
    modes

