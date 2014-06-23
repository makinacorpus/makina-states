{#-
# icinga
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_nagvis.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.nagvis.hooks
  - makina-states.services.monitoring.nagvis.services


# general configuration
nagvis-conf:
  file.managed:
    - name: {{data.configuration_directory}}/nagvis.ini.php
    - source: salt://makina-states/files/etc/nagvis/nagvis.ini.php
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: nagvis-pre-conf
    - watch_in:
      - mc_proxy: nagvis-post-conf
    - defaults:
      data: |
            {{sdata}}


{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{#
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
