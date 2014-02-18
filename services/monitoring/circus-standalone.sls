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
{%- set locs = localsettings.locations %}
{%- set circusSettings = services.circusSettings %}

{%- set venv = circusSettings['location'] + "/venv" %}

{%- if full %}
{#- Install circus #}
circus-install-virtualenv:
  virtualenv.managed:
    - name: {{ venv }}

circus-install-pkg:
  pip.installed:
    - name: circus==0.10.0
    - bin_env: {{ venv }}/bin/pip
    - require:
      - virtualenv: circus-install-virtualenv
    - require_in:
      - file: circus-setup-conf
      - file: circus-setup-conf-include-directory
      - cmd: circus-start
{%- endif %}

{#- Configuration #}
circus-setup-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/circus.ini
    - source: salt://makina-states/files/etc/circus.ini
    - template: jinja
    - defaults:
        conf_dir: {{ locs['conf_dir'] }}

circus-setup-conf-include-directory:
  file.directory:
    - name: {{ locs['conf_dir'] }}/circus.conf.d

{#- Run #}
circus-start:
  cmd.run:
    - name: . {{ venv }}/bin/activate && {{ venv }}/bin/circusd --daemon {{ locs['conf_dir'] }}/circus.ini

{% endmacro %}
{{ do(full=False) }}

{% macro circusAddWatcher(name, cmd, args="", extras="") %}
circus-add-watcher-{{ name }}:
  file.managed:
    - name: {{ locs['conf_dir'] }}/circus.conf.d/watcher-{{ name }}.ini
    - source: salt://makina-states/files/etc/circus.conf.d/watcher.ini
    - template: jinja
    - defaults:
        name: {{ name }}
        cmd: {{ cmd }}
        args: {{ args }}
        extras: {{ extras }}
    - require:
        - file: circus-setup-conf
        - file: circus-setup-conf-include-directory
    - require_in:
        - cmd: circus-start
{% endmacro %}
