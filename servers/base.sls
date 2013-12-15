{% import "makina-states/_macros/salt.jinja" as c with context %}
#
# Idea is for a machine to be managed only to have to do
#
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
# To better understand how things are done
#
# Tree of different configuration flavors inheritance
#
#  vm   devhost
#   |       |        salt master       mastersalt master
#   |_______|            |             /
#      |             salt minon       | mastersalt minion
#      server            |            |/
#      |_________________|____________|      dockercontainer  lxcontainer
#             |____________________________________________|__|
#             |
#            base
#             |
#        services:base
###########################################################################

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


