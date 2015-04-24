{#-
# Circus
#
# You only need to drop a configuration file in the include dir to add a watcher.
# Please see the circusAddWatcher macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set defaults = salt['mc_circus.settings']() %}
{%- set venv = defaults['venv'] %}
include:
  - makina-states.services.monitoring.circus.hooks
  - makina-states.services.monitoring.circus.services

{#- Run #}
{% if grains['os'] in ['Ubuntu'] %}


{% set extra_confs = {
  '/usr/bin/circus.sh': {"mode": "755"},
  '/etc/systemd/system/circusd.service': {"mode": "644"}
}%}
{% for i, cdata in extra_confs.items() %}
circus-{{i}}:
  file.managed:
    - name: {{i}}
    - source: salt://makina-states/files{{i}}
    - mode: {{cdata.mode}}
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf
{% endfor %}

circus-upstart-conf:
  file.managed:
    - name: /etc/init/circusd.conf
    - source: salt://makina-states/files/etc/init/circusd.conf
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf

{% else %}
circus-init-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/circusd
    - source: salt://makina-states/files/etc/init.d/circusd
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf
{% endif %}

circus-initdef-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/default/circusd
    - source: salt://makina-states/files/etc/default/circusd
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - makedirs: true
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf

circus-setup-conf-directories:
  file.directory:
    - names:
      -  {{ locs['conf_dir'] }}/circus/circusd.conf.d
      -  {{ defaults.logdir }}
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf

circus-logrotate:
  file.managed:
    - name: {{ locs['conf_dir'] }}/logrotate.d/circus.conf
    - source: salt://makina-states/files/etc/logrotate.d/circus.conf
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-pre-restart

{#- Configuration #}
circus-setup-conf:
  file.managed:
    - name: {{defaults.conf}}
    - source: salt://makina-states/files/etc/circus/circusd.ini
    - makedirs: true
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf

circus-ms_circusctl:
  file.managed:
    - name: {{defaults.venv}}/bin/ms_circusctl
    - source: ''
    - template: jinja
    - user: root
    - makedirs: true
    - group: root
    - mode: 700
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-pre-restart
    - contents: |
                #!/usr/bin/env bash
                . {{defaults.venv}}/bin/activate
                {{defaults.venv}}/bin/circusctl \
                "$@"

{% for i in ['circusd', 'circusctl', 'ms_circusctl'] %}
file-symlink-{{i}}:
  file.symlink:
    - target: {{defaults.venv}}/bin/{{i}}
    - name: /usr/local/bin/{{i}}
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-pre-restart
{% endfor %}

circus-globalconf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/circus/circusd.conf.d/010_global.ini
    - source: salt://makina-states/files/etc/circus/circusd.conf.d/010_global.ini
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf

{%- import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{#
{{circus.circusAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
