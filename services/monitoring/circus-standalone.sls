{#-
# Circus
# Read the circus section of _macros/services.jinja to know which grain/pillar settings
# can modulate your circus installation
#
# You only need to drop a configuration file in the include dir to add a watcher.
# Please see the circusAddWatcher macro at the end of this file.
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}

{%- macro do(full=True) %}
{{- salt['mc_macros.register']('services', 'monitoring.circus') }}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = salt['mc_localsettings']()['locations'] %}
{%- set circusSettings = services.circusSettings %}
{%- set venv = circusSettings['location'] + "/venv" %}
{% set defaults = {
  'extra': circusSettings,
  'log': locs.var_log_dir+'/circus.log',
  'locs': locs,
  'venv': venv,
  'pidf': locs.var_run_dir+'/circusd.pid',
} %}

include:
  - makina-states.services.monitoring.circus-hooks

{%- if full %}
{#- Install circus #}
circus-install-virtualenv:
  virtualenv.managed:
    - name: {{ venv }}

circus-install-pkg:
  file.managed:
    - name: /etc/circus/requirements.txt
    - source: ''
    - contents: >
                {{'\n                 '.join(circusSettings['requirements'])}}
    - user: root
    - group: root
    - mode: 750
  pip.installed:
    - requirements: /etc/circus/requirements.txt
    - bin_env: {{ venv }}/bin/pip
    - require:
      - file: circus-install-pkg
      - virtualenv: circus-install-virtualenv
    - require_in:
      - file: circus-setup-conf
      - file: circus-setup-conf-include-directory
      - mc_proxy: circus-pre-restart
{%- endif %}

{#- Configuration #}
circus-setup-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/circus/circusd.ini
    - source: salt://makina-states/files/etc/circus/circusd.ini
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: circus-pre-restart
    - defaults:
        conf_dir: {{ locs['conf_dir'] }}

circus-globalconf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/circus/circusd.conf.d/010_global.ini
    - source: salt://makina-states/files/etc/circus/circusd.conf.d/010_global.ini
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: circus-pre-restart
    - defaults: {{defaults|yaml}}

circus-setup-conf-include-directory:
  file.directory:
    - name: {{ locs['conf_dir'] }}/circus/circusd.conf.d
    - watch_in:
      - mc_proxy: circus-pre-restart

circus-logrotate:
  file.managed:
    - name: {{ locs['conf_dir'] }}/logrotate.d/circus.conf
    - source: salt://makina-states/files/etc/logrotate.d/circus.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: circus-pre-restart
    - defaults: {{defaults|yaml}}

{#- Run #}
{% if grains['os'] in ['Ubuntu'] %}
circus-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/circusd.conf
    - source: salt://makina-states/files/etc/init/circusd.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: circus-pre-restart
    - defaults: {{defaults|yaml}}
{% else %}
circus-init-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/circusd
    - source: salt://makina-states/files/etc/init.d/circusd
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: circus-pre-restart
    - defaults: {{defaults|yaml}}
{% endif %}


circus-initdef-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/default/circusd
    - source: salt://makina-states/files/etc/default/circusd
    - template: jinja
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: circus-pre-restart
    - defaults: {{defaults|yaml}}

circus-start:
  service.running:
    - name: circusd
    - enable: True
    - watch:
      - mc_proxy: circus-pre-restart
    - watch_in:
      - mc_proxy: circus-post-restart

{% endmacro %}
{{ do(full=False) }}
