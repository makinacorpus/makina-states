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

# configure databases
icinga_web-databases-conf:
  file.managed:
    - name: {{data.configuration_directory}}/conf.d/databases.xml
    - source: salt://makina-states/files/etc/icinga-web/conf.d/databases.xml
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

icinga_web-access-conf:
  file.managed:
    - name: {{data.configuration_directory}}/conf.d/access.xml
    - source: salt://makina-states/files/etc/icinga-web/conf.d/access.xml
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



# not used
{#
#
#{% if grains['os'] in ['Ubuntu'] %}
#icinga-init-conf:
#  file.managed:
#    - name: {{ locs['conf_dir'] }}/init/ms_icinga.conf
#    - source: salt://makina-states/files/etc/init/ms_icinga.conf
#    - template: jinja
#    - user: root
#    - makedirs: true
#    - group: root
#    - mode: 755
#    - watch:
#      - mc_proxy: icinga-pre-conf
#    - watch_in:
#      - mc_proxy: icinga-post-conf
#    - defaults:
#      data: |
#            {{salt['mc_utils.json_dump'](defaults)}}
#{% else %}
#icinga-init-conf:
#  file.managed:
#    - name: {{ locs['conf_dir'] }}/init.d/ms_icinga
#    - source: salt://makina-states/files/etc/init.d/ms_icinga
#    - template: jinja
#    - user: root
#    - makedirs: true
#    - group: root
#    - mode: 755
#    - watch:
#      - mc_proxy: icinga-pre-conf
#    - watch_in:
#      - mc_proxy: icinga-post-conf
#    - defaults:
#      data: |
#            {{salt['mc_utils.json_dump'](defaults)}}
#{% endif %}
#
#icinga-setup-conf-directories:
#  file.directory:
#    - names:
#      -  {{ locs['conf_dir'] }}/icinga.d
#      -  {{ defaults.icingad.logdir }}
#    - watch:
#      - mc_proxy: icinga-pre-conf
#    - watch_in:
#      - mc_proxy: icinga-post-conf
#
#icinga-logrotate:
#  file.managed:
#    - name: {{ locs['conf_dir'] }}/logrotate.d/icinga.conf
#    - source: salt://makina-states/files/etc/logrotate.d/icinga.conf
#    - template: jinja
#    - user: root
#    - makedirs: true
#    - group: root
#    - mode: 755
#    - watch:
#      - mc_proxy: icinga-pre-conf
#    - watch_in:
#      - mc_proxy: icinga-pre-restart
#    - defaults:
#        data: |
#              {{salt['mc_utils.json_dump'](defaults)}}
#
#icinga-ms_icingactl:
#  file.managed:
#    - name: {{defaults.venv}}/bin/ms_icingactl
#    - source: ''
#    - template: jinja
#    - user: root
#    - makedirs: true
#    - group: root
#    - mode: 700
#    - watch:
#      - mc_proxy: icinga-pre-conf
#    - watch_in:
#      - mc_proxy: icinga-pre-restart
#    - contents: |
#                #!/usr/bin/env bash
#                . {{defaults.venv}}/bin/activate
#                {{defaults.venv}}/bin/icingactl \
#                  -c "{{defaults.conf}}" \
#                  -u "{{defaults.icingactl.username}}"\
#                  -p "{{defaults.icingactl.password}}" "$@"
#    - defaults:
#        data: |
#              {{salt['mc_utils.json_dump'](defaults)}}
#
#{% for i in ['icingad', 'icingactl', 'ms_icingactl'] %}
#file-symlink-{{i}}:
#  file.symlink:
#    - target: {{defaults.venv}}/bin/{{i}}
#    - name: /usr/local/bin/{{i}}
#    - watch:
#      - mc_proxy: icinga-pre-conf
#    - watch_in:
#      - mc_proxy: icinga-pre-restart
#{% endfor %}
#
#
#}
{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{#
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
