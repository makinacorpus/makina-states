{% import "makina-states/_macros/h.jinja" as h with context %}
{#-
# Circus
# You only need to drop a configuration file in the include dir to add a watcher.
# Please see the circusAddWatcher macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set defaults = salt['mc_circus.settings']() %}
{%- set venv = defaults['venv'] %}
include:
  - makina-states.services_managers.circus.hooks
  - makina-states.services_managers.circus.services


{# deliver initd & default twice, as we should early stop circus
   when we are in upstart mode #}
{% macro rmacro() %}
    - require:
      - mc_proxy: circus-post-install
    - require_in:
      - cmd: circusd-upstart-cleanup
{% endmacro %}
{% set upstartcfg = {} %}
{% for a, cfg in defaults.configs.items() %}
{% if a in ['/etc/default/circusd',
            '/etc/init.d/circusd',
            ]%}
{% do upstartcfg.update({a: cfg}) %}
{% endif %}
{% endfor %}
{{ h.deliver_config_files(
     upstartcfg, after_macro=rmacro, prefix='circus-upstart-conf-')}}

{% macro rmacro() %}
    - watch:
      - file: circus-setup-conf-directories
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf
{% endmacro %}
{{ h.deliver_config_files(
     defaults.configs, after_macro=rmacro, prefix='circus-conf-')}}

{% if grains['oscodename'] in ['trusty'] %}
circusd-upstart-cleanup:
  cmd.run:
    - name: service circusd stop
    - onlyif: test -e /etc/init/circusd.conf && which circusctl
    - require:
      - mc_proxy: circus-post-install
  file.absent:
    - names:
      - /etc/init/circusd.conf
    - require:
      - cmd: circusd-upstart-cleanup
    - require_in:
      - mc_proxy: circus-pre-conf
{% endif %}

circus-setup-conf-directories:
  file.directory:
    - names:
      - {{ locs['conf_dir'] }}/circus/circusd.conf.d
      - {{ defaults.logdir }}
    - mode: 755
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-post-conf

{% for i in ['circusd', 'circusctl'] %}
file-symlink-{{i}}:
  file.symlink:
    - target: {{defaults.venv}}/bin/{{i}}
    - name: /usr/local/bin/{{i}}
    - watch:
      - mc_proxy: circus-pre-conf
    - watch_in:
      - mc_proxy: circus-pre-restart
{% endfor %}
{%- import "makina-states/services_managers/circus/macros.jinja" as circus with context %}
{# {{circus.circusAddWatcher('foo', '/bin/echo', args=[1]) }} #}
