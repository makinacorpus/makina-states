{#-
# supervisor
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set defaults = salt['mc_supervisor.settings']() %}
{%- set venv = defaults['venv'] %}
include:
  - makina-states.services.monitoring.supervisor.hooks
  - makina-states.services.monitoring.supervisor.services

supervisord-conf:
  file.managed:
    - name: {{defaults.conf}}
    - source: {{defaults.conf_template}}
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 700
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf

{% set extra_confs = {
  '/usr/bin/ms_supervisor.sh': {"mode": "755"},
  '/etc/systemd/system/ms_supervisor.service': {"mode": "644"}
}%}

{% for i, cdata in extra_confs.items() %}
supervisor-{{i}}:
  file.managed:
    - name: {{i}}
    - source: salt://makina-states/files{{i}}
    - mode: {{cdata.mode}}
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf
{% endfor %}

{% if grains['os'] in ['Ubuntu'] %}
supervisor-init-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/ms_supervisor.conf
    - source: salt://makina-states/files/etc/init/ms_supervisor.conf
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf

{% else %}
supervisor-init-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/ms_supervisor
    - source: salt://makina-states/files/etc/init.d/ms_supervisor
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf
{% endif %}

supervisor-setup-conf-directories:
  file.directory:
    - names:
      -  {{ locs['conf_dir'] }}/supervisor.d
      -  {{ defaults.supervisord.logdir }}
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf

supervisor-logrotate:
  file.managed:
    - name: {{ locs['conf_dir'] }}/logrotate.d/supervisor.conf
    - source: salt://makina-states/files/etc/logrotate.d/supervisor.conf
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-pre-restart

supervisor-ms_supervisorctl:
  file.managed:
    - name: {{defaults.venv}}/bin/ms_supervisorctl
    - source: ''
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 700
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-pre-restart
    - contents: |
                #!/usr/bin/env bash
                . {{defaults.venv}}/bin/activate
                {{defaults.venv}}/bin/supervisorctl \
                  -c "{{defaults.conf}}" \
                  -u "{{defaults.supervisorctl.username}}"\
                  -p "{{defaults.supervisorctl.password}}" "$@"
    - defaults:
        data: |
              {{salt['mc_utils.json_dump'](defaults)}}

{% for i in ['supervisord', 'supervisorctl', 'ms_supervisorctl'] %}
file-symlink-{{i}}:
  file.symlink:
    - target: {{defaults.venv}}/bin/{{i}}
    - name: /usr/local/bin/{{i}}
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-pre-restart
{% endfor %}


{%- import "makina-states/services/monitoring/supervisor/macros.jinja" as supervisor with context %}
{#
{{supervisor.supervisorAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
