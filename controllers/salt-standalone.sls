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
{%- import "makina-states/controllers/salt-hooks.sls" as base with context %}
{%- set controllers   = base.controllers %}
{%- set saltmac       = base.saltmac %}
{%- set name          = base.name %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  - makina-states.services.cache.memcached.hooks
  {% if full %}
  - makina-states.localsettings
  {% endif %}
  - makina-states.controllers.salt-hooks
{{ saltmac.install_makina_states(name, full=full) }}
{% endmacro  %}
{{ do(full=False)}}
