# As described in wiki each server has a local master
# This state file only install makina-states
# base layout
# but can also be controlled via the mastersalt
# We have the local master in /etc/salt
# and another dedicated to sysadmin called mastersalt::
#
#   - file_root: /srv/mastersalt
#   - pillar_root: /srv/mastersalt-pillar
#   - conf: /etc/mastersalt
#   - sockets: /var/run/mastersalt-*
#   - logs: /var/logs/salt/mastersalt-*
#   - services: mastersalt-minon & mastersalt-master
#
# binaries:
#   - /usr/bin/mastersalt
#   - /usr/bin/mastersalt-key
#   - /usr/bin/mastersalt-call
#   - /usr/bin/mastersalt-master
#   - /usr/bin/mastersalt-minion
#
# We create a group called editor which has rights in /srv/{pillar, salt, projects}
{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% set controllers = controllers %}
{% set localsettings = controllers.localsettings %}
{% set saltmac = controllers.saltmac %}
{% set name = saltmac.msaltname %}
{{ controllers.register(name) }}

include:
  - {{ controllers.funcs.statesPref }}localsettings

{{ saltmac.install_makina_states(name) }}
