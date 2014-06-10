{#-
# icinga
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set defaults = salt['mc_icinga.settings']() %}
{%- set venv = defaults['venv'] %}
include:
  - makina-states.services.monitoring.icinga.hooks
  - makina-states.services.monitoring.icinga.services

icinga-conf:
  file.managed:
    - name: /etc/icinga/icinga.cfg
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
            {{salt['mc_utils.json_dump'](defaults)}}


{% if defaults.modules.ido2db.enabled %}

io2db-conf:
  file.managed:
    - name: /etc/icinga/ido2db.cfg
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
            {{salt['mc_utils.json_dump'](defaults)}}

iomod-conf:
  file.managed:
    - name: /etc/icinga/idomod.cfg
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
            {{salt['mc_utils.json_dump'](defaults)}}

{% endif %}


# not used

{% if grains['os'] in ['Ubuntu'] %}
icinga-init-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/ms_icinga.conf
    - source: salt://makina-states/files/etc/init/ms_icinga.conf
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](defaults)}}
{% else %}
icinga-init-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/ms_icinga
    - source: salt://makina-states/files/etc/init.d/ms_icinga
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](defaults)}}
{% endif %}

icinga-setup-conf-directories:
  file.directory:
    - names:
      -  {{ locs['conf_dir'] }}/icinga.d
      -  {{ defaults.icingad.logdir }}
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-logrotate:
  file.managed:
    - name: {{ locs['conf_dir'] }}/logrotate.d/icinga.conf
    - source: salt://makina-states/files/etc/logrotate.d/icinga.conf
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-pre-restart
    - defaults:
        data: |
              {{salt['mc_utils.json_dump'](defaults)}}

icinga-ms_icingactl:
  file.managed:
    - name: {{defaults.venv}}/bin/ms_icingactl
    - source: ''
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 700
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-pre-restart
    - contents: |
                #!/usr/bin/env bash
                . {{defaults.venv}}/bin/activate
                {{defaults.venv}}/bin/icingactl \
                  -c "{{defaults.conf}}" \
                  -u "{{defaults.icingactl.username}}"\
                  -p "{{defaults.icingactl.password}}" "$@"
    - defaults:
        data: |
              {{salt['mc_utils.json_dump'](defaults)}}

{% for i in ['icingad', 'icingactl', 'ms_icingactl'] %}
file-symlink-{{i}}:
  file.symlink:
    - target: {{defaults.venv}}/bin/{{i}}
    - name: /usr/local/bin/{{i}}
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-pre-restart
{% endfor %}


{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{#
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
