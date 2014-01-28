{#-
# Salt base installation
# We set
#   - file_root: /srv/salt
#   - pillarRoot: /srv/pillar
#   - conf: /etc/salt
#   - projects code source: /srv/projects
#   - sockets: /var/run/{master, minion}
#   - logs: /var/logs/salt/{master, minion}(key*)
#   - services: salt-minon & salt-master
#
# binaries:
#   - /usr/bin/salt
#   - /usr/bin/salt-key
#   - /usr/bin/salt-call
#   - /usr/bin/salt-master
#   - /usr/bin/salt-minion
#
# This state file only install makina-states
# base layout
#
# We create a group called editor which has rights in /srv/{pillar, salt, projects}
#
#
# Base server which acts also as a mastersalt master
#}
{%- import "makina-states/_macros/controllers.jinja" as controllers with context %}
{%- set controllers = controllers %}
{%- set localsettings = controllers.localsettings %}
{%- set saltmac = controllers.saltmac %}
{%- set name = saltmac.saltname %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  - makina-states.localsettings
{{ saltmac.install_makina_states(name) }}
