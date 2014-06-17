{#-
# icinga
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_cgi.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.icinga_cgi.hooks
  - makina-states.services.monitoring.icinga_cgi.services

# general configuration
icinga_cgi-conf:
  file.managed:
    - name: {{data.configuration_directory}}/cgi.cfg
    - source: salt://makina-states/files/etc/icinga-cgi/cgi.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga_cgi-pre-conf
    - watch_in:
      - mc_proxy: icinga_cgi-post-conf
    - defaults:
      data: |
            {{sdata}}


{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{#
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
