{% import "makina-states/_macros/vars.jinja" as c with context %}
{% import "makina-states/_macros/salt.jinja" as s with context %}
#
# Idea is for a machine to be managed only to have to includes setups which apply:
# - a set of configuration
# - a grain to flag the machine as using this configuration to store for
#   later reconfigurations
#
# There a a lot of variables that can modify the configurationa applied to a minion.
# To find what to do, read the states that seem to be tied to your needs.
# You can alsohave a look to _macros/vars.sls and _macros/_salt.sls which are the two
# most importants macros of this installation. They expose a lot of those variables
# for the underlying states to react on that stuff.
# base:
#   minionid:
#     - makina-states.servers.base
#
# When you do that, it will automaticly put the base configuration
# on your box depending on how you have taggued it.
# As grains are particulary insecures, pay attention that states chained
# by this inheritance are only limited to the base installation
# and do not expose too much sensitive data coming from associated pillars
#
# To better understand how things are done, tis is an non exhaustive graph
# or our states tree
#
# Tree of different configuration flavors inheritance
#
#
#     vm   devhost
#      |       |        salt master       mastersalt master
#      |_______|            |             /
#         |             salt minon       | mastersalt minion
#         server            |            |/
#         |_________________|____________|
#                |
#              SERVERBASE
#                |
#          ______|______________   tomcat
#         |                     | /_____ solr
#         |   base/service:base | |java       dockercontainer  lxcontainer
#         |_____________________| |       virt /________________/
#                          \      |           |
#     ______________________\_____/___________|__________
#    /   | |    |   |     |       | |  |                |
#    lxc | ldap | salt/mastersalt | |  |    .-- nginx   |
#        |  |   |                 | |  |   /__ apache   |
#        | nscd |                ssh|  http             php____ phpfpm
#        |      |                   |                      |
#        |      |                   |                      modphp
#        db   mail                  |
#        /\     \                   shorewall
#       /  \     \____ postfix
#    pgsql  mysql \
#                  \__ dovecot
#


{% set nomatch = False %}
{% set mastersalt_nomatch = False %}
include:
  - makina-states.services.base
  {% if c.vm %}- makina-states.servers.vm
  {% elif c.devhost %}- makina-states.servers.devhost
  {% elif c.server %}- makina-states.servers.server
  {% elif c.salt_master %}- makina-states.servers.salt_master
  {% elif c.salt_minion %}- makina-states.servers.salt_minion
  {% else %}{% set nomatch = True %}{% endif %}
  {% if c.mastersalt_master %}- makina-states.servers.mastersalt_master
  {% elif c.mastersalt_minion %}- makina-states.servers.mastersalt_minion
  {% else %}{% set mastersalt_nomatch = True %}{% endif %}
  {% if ((not c.docker) and c.lxc) %}- makina-states.servers.lxccontainer
  {% elif (c.docker) %}- makina-states.servers.dockercontainer {% endif %}


