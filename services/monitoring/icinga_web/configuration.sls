{#-
# icinga
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_web.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.icinga_web.hooks
  - makina-states.services.monitoring.icinga_web.services

{% for file in ['access', 'auth', 'cronks', 'databases', 'exclude_customvars', 'factories', 'icinga', 'logging', 'module_appkit', 'module_cronks', 'module_reporting', 'module_web', 'settings', 'sla', 'translation', 'userpreferences', 'views'] %}
icinga_web-{{file}}-conf:
  file.managed:
    - name: {{data.configuration_directory}}/conf.d/{{file}}.xml
    - source: salt://makina-states/files/etc/icinga-web/conf.d/{{file}}.xml
    - template: jinja
    - makedirs: true
    - user: root
    - group: www-data
    - mode: 640
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf
    - defaults:
      data: |
            {{sdata}}
{% endfor %}

# sometimes, the password in /usr/share/icinga-web/config/databases.xml is not updated
# "I noticed that /etc/icinga-web doesn't seem to be parsed. at the very least, /etc/icinga-web/databases.xml doesn't seem to be."
# manually update
icinga_web-usr-databases-conf:
  file.managed:
    - name: /usr/share/icinga-web/app/config/databases.xml
    - source: salt://makina-states/files/etc/icinga-web/databases-usr.xml
    - template: jinja
    - makedirs: true
    - user: root
    - group: www-data
    - mode: 640
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf
    - defaults:
      data: |
            {{sdata}}

# clear cache
icinga_web-clear-cache:
  cmd.run:
    - name: rm -f /var/cache/icinga-web/config/*
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf

{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{#
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
