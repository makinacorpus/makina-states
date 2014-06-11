{#-
# icinga
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.icinga.hooks
  - makina-states.services.monitoring.icinga.services

# general configuration
icinga-conf:
  file.managed:
    - name: {{data.configuration_directory}}/icinga.cfg
    - source: salt://makina-states/files/etc/icinga/icinga.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}


# startup configuration
{% if grains['os'] in ['Ubuntu'] %}

icinga-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/icinga.conf
    - source: salt://makina-states/files/etc/init/icinga.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

{% else %}

icinga-init-default-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/etc/default
    - source: salt://makina-states/files/etc/default/icinga
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

icinga-init-sysvinit-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/icinga
    - source: salt://makina-states/files/etc/init.d/icinga
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

{% endif %}

# modules configuration
{% if data.modules.ido2db.enabled %}

ido2db-conf:
  file.managed:
    - name: {{data.configuration_directory}}/ido2db.cfg
    - source: salt://makina-states/files/etc/icinga/ido2db.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

idomod-conf:
  file.managed:
    - name: {{data.configuration_directory}}/idomod.cfg
    - source: salt://makina-states/files/etc/icinga/idomod.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

# IDO database schema should be created here

{% if 'pgsql' == data.modules.ido2db.database.type %}
ido2db-create-pgsql-user:
  postgres.user_create:
    - username: {{data.modules.ido2db.database.user}}
    - rolepassword: {{data.modules.ido2db.database.password}}


#ido2db-create-pgsql-database:
#ido2db-import-pgsql-schema:

{% elif 'mysql' == data.modules.ido2db.database.type %}
#ido2db-create-mysql-user:
#ido2db-create-mysql-database:
#ido2db-import-mysql-schema:

{% endif %}

# startup ido2db configuration
{% if grains['os'] in ['Ubuntu'] %}

ido2db-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/ido2db.conf
    - source: salt://makina-states/files/etc/init/ido2db.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

{% else %}

ido2db-init-sysvinit-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/ido2db
    - source: salt://makina-states/files/etc/init.d/ido2db
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

{% endif %}

{% endif %}



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
