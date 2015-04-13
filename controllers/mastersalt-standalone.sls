{#-
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
#}
{%- import "makina-states/controllers/mastersalt-hooks.sls" as base%}
{%- set controllers   = base.controllers %}
{%- set saltmac       = base.saltmac %}
{%- set name          = base.name %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  {% if full %}
  - makina-states.services.cache.memcached
  - makina-states.localsettings
  {% endif %}
  - makina-states.localsettings.git
  - makina-states.controllers.hooks
  - makina-states.services.cache.memcached.hooks
{{ saltmac.install_makina_states(name, full=full) }}
{% endmacro  %}
{{ do(full=False)}}
