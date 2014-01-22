{#
# Idea is for a machine to be managed only to have to have either to:
#
#   - Set tags in pillar or grains or configuration
#   - Include directly a specific state
#
# As soon as those tags are run, they will set a grain on the machine
# having the side effect to register that part of our states to be 'auto installed'
#in the future highstates, they will even run even if we have not included them explicitly.
#
# TODO:
#   - We are planning the uninstall part but it is not yet done
#   - In the meantime, to uninstall a state, you ll have first to remove the grain/pillar/inclusion
#     Then rerun the highstate and then code a specific cleanup sls file if you want to cleanup
#     what what left on the server
#
# As you certainly have understood, this is to enable some kind of local auto configuration
# based on previous runs and on configuration (grains + states inclusions + pillar).
# All this configuration is stored in macros used by all the states, look at ./_macros.
#
# To sum up, we have made all of those states reacting and setting tags for the system
# to be totally dynamic. All the things you need to do is to set in pillar or in grains
# the appropriate values for your machine to be configured.
#
# In othe words, you have 4 levels to make salt install you a 'makina state'
# which will be automaticly included in the next highstate
#
#   - Direct inclusion via the 'include:' statement:
#       - include makina-states.services.http.apache
#   - Install directly the state via a salt/salt-call state.sls
#       - salt-call state.sls makina-states.services.http.apache true
#   - Appropriate grain configuration slug
#       - salt-call --local grains.setval makina-states.services.http.apache true
#   - Appropriate pillar configuration slug
#       - makina-states.services.http.apache: true in a pillar file
#   - Run the highstate, and as your machine is taggued, apache
#     will be installed
#
# You can imagine that there a a lot of variables that can modify the configurationa applied to a minion.
# To find what to do, we invite you to just read the states that seem to be relevant to your needs.
# You can also have a look to _macros/*.jinja files.
#
# As grains are particulary insecures, pay attention that states chained
# by this inheritance are only limited to the base installation
# and do not expose too much sensitive data coming from associated pillars
#
# To better understand how things are done, this is an non exhaustive graph
# or our states tree:
#
# Tree of different configuration flavors inheritance
#                                                                      C
#                                                                      O
#                                                                      N
# ^-- NODETYPES ---- controlled- ->| salt-minion   - mastersalt-minion T
# ^                      by        |      ^        -        ^          R
# ^                    one of      |      ^        -        ^          O
# ^                      -         |   controlling -    controlling    L
# ^                      -         |      ^        -        ^          L
# ^ ------lxc            -         | salt-master   - mastersalt-master E
# ^ |                    -         |____________________    ^          R
# ^ |                    -                                  ^          S
# ^ |---- docker         -------------->>>>>>---------------^
# ^ |     -container
# ^ |
# ^ |  vagrantvm                   ________________
# ^ |     |                        [               ]
# ^ vm devhost      installed <----[  server:base  ] <- begin to  << ---
# ^  \   /              on         [ configuration ]    read here << ---
# |   \ /              a           [_______________]       ^
# |-- server <----- NODETYPE            |        |         ^
#                                       |        |         |
#                                       |        |         |
#                running on ----->>>>>>>^        |
#                   ^                            |
#                   ^                            |
#                   ^                            |
#                   ^                            |-----------------> LOCALSETTINGS
#         __________^___________   solr                             ldap nscd profile
#        |                     |      |    lxc                      vim git sudo localrc
#        |   service:base      | tomcat    |                        pkgs pkgmgr shell
#        |_____________________|      |    docker                   users
#                          ^     java |
#            bacula-fd     ^          |    virt
#                |   ntp   ^          |    |
#      __________|___|_____^__________|____|________
#      | |    |   |     |  ^    | |  |              \
#      | ldap | salt/mastersalt | |  |    .-- nginx  |
#      |  |   |                 | |  |   /__ apache  |
#      | nscd |                ssh|  http            php____ phpfpm
#      |      |                   |                       |
#      |      |                   |                       modphp
#      db   mail                  |
#      /\     \                   shorewall
#     /  \     \____ postfix
#  pgsql  mysql \
#                \__ dovecot
#
#
# You may have already note that there are some main kind of tags
#   - server nodetypes: which server do i run on
#   - 2 kinds of salt controllers (salt/mastersalt)
#       * salt is a local project salt master
#       * mastersalt is the salt master of the admin guys
#   - services
#
# Some rules to write makina-states states:
#   - Learn and use the [Kind]register mecanism. (its a one liner saving your ass)
#   - Never ever write an absolute path, use localsettings.locations.PATH_PREFIX
#   - If your path is not in that mapping and is enoughtly generic, just add it.
#   - Never ever use short form of states (states without names)
#   - Please use as much as possible require(_in)/watch(_in) to ensure your configuration
#     slugs will be correctly scheduled
#   - Use CamelCase for variables names for them to not been marked as jinja private variables
#   - On the contrary, use _underscore_case for very private macros variables
#
# The default general order of inclusion is as follow:
#
#   - Local settings
#   - Controllers
#   - Nodes Types
#   - Services
#}
# And here is the point where all the things start to work together...
{% import "makina-states/_macros/funcs.jinja" as funcs with context %}
# This loop includes all the kind of things that could be installed
include:
{% for kind in funcs.kinds -%}
  - {{funcs.statesPref}}{{kind}}
{% endfor %}
