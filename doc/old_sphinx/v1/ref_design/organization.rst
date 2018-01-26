Main states kind segregation
=============================
Overview
--------
In makina states we have organised our states in the following way:

    :controllers: states related to the base salt infrastructure (layout, deamons, permissions)
    :nodetypes: states related only to the hardware, the machine type  or virtualisation facillity
    :localsettings: states related to the base machine configuration minus all that can looks like a service or a deamon (eg: directories creations, hosts managment, pam, vim but not ssh)
    :services: states related to services configuration (eg: ssh, docker, apache, backups scripts & crons)
    :projects: Set of macros to be externallly included project consumers as the base to setup their projects using makina-states bricks
    :cloud: set of related stuff linked to mastersalt salt cloud integration

For all those kinds, we have execution modules, sub-execution modules and formulaes containers. to leverage and factorize all variables and have well placed macros.

For exemple, php users will certainly have to deal the following files:

    :mc_states/modules/services.py: registries
    :mc_states/services/{http,php}/\*.sls: states files (formulaes)
    :/srv/pillar/foo.sls: custom settings

Wrap-up
-------
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
     configuration |                                                ------------------------------
    --+--------+---+                                                |   makina-states.cloud      |
      |        |                                                    ------------------------------
      |        |            +---------------+                         |___ generic
      |        |            |               |  solr                   |___ lxc   
      |     running on <----+ Service:base  |   |                     |___ saltify
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
        /\     \                   firewalld
       /  \     \____ postfix
    pgsql  mysql \
                  \__ dovecot




