{% import "makina-states/_macros/h.jinja" as h with context %}
{#-
# supervisor
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}
{% set locs = salt['mc_locations.settings']() %}
{% set defaults = salt['mc_supervisor.settings']() %}
{%- set venv = defaults['venv'] %}
include:
  - makina-states.services.monitoring.supervisor.hooks
  - makina-states.services.monitoring.supervisor.services

{% macro rmacro() %}
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf
{% endmacro %}
{{ h.deliver_config_files(
     defaults.configs, after_macro=rmacro, prefix='supervisor-conf-')}}

supervisor-setup-conf-directories:
  file.directory:
    - names:
      -  {{ locs['conf_dir'] }}/supervisor.d
      -  {{ defaults.supervisord.logdir }}
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf

supervisor-cleanup:
  file.absent:
    - names:
      - /etc/init/ms_supervisor.conf
    - watch:
      - mc_proxy: supervisor-pre-conf
    - watch_in:
      - mc_proxy: supervisor-post-conf

{% for i in ['supervisord', 'supervisorctl'] %}
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
{# {{supervisor.supervisorAddWatcher('foo', '/bin/echo', args=[1]) }} #}
