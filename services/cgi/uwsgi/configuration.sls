{#-
# uwsgi
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_uwsgi.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.cgi.uwsgi.hooks
  - makina-states.services.cgi.uwsgi.services

# TODO upstart script for uwsgi

{#
{%- import "makina-states/services/cgi/uwsgi/macros.jinja" as uwsgi with context %}
#}
{#
{{uwsgi.uwsgiAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
