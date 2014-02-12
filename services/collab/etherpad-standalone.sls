{#-
# Etherpad server: https://github.com/ether/etherpad-lite
# Read the etherpad section of _macros/services.jinja to know which grain/pillar settings
# can modulate your etherpad installation
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}

{%- macro do(full=True) %}
{{- salt['mc_macros.register']('services', 'collab.etherpad') }}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = localsettings.locations %}
{%- set etherpadSettings = services.etherpadSettings %}

{%- set etherpadLocation = etherpadSettings['location'] + "/etherpad-lite-" + etherpadSettings['version'] %}

{% import "makina-states/localsettings/nodejs-standalone.sls" as nodejs with context %}
{{ nodejs.do(full=full) }}

{%- if full %}
etherpad-create-user:
  user.present:
    - name: etherpad
    - shell: /bin/bash
    - gid_from_name: True
    - remove_groups: False
    - require:
        - pkg: nodejs-pkgs

{#- Download and install etherpad #}
etherpad-create-directory:
  file.directory:
    - name: {{ etherpadSettings['location'] }}
    - dir_mode: 755
    - makedirs: True

etherpad-install-pkg:
  file.directory:
    - name: {{ etherpadSettings['location'] }}
    - user: etherpad
    - group: etherpad
    - recurse:
        - user
        - group
  cmd.run:
    - name: >
          wget https://github.com/ether/etherpad-lite/archive/{{ etherpadSettings['version'] }}.zip
          && unzip {{ etherpadSettings['version'] }}.zip
          && rm {{ etherpadSettings['version'] }}.zip
    - cwd: {{ etherpadSettings['location'] }}
    - user: etherpad
    - group: etherpad
    - require:
      - user: etherpad
      - file: etherpad-create-directory
    - require_in:
      - file: etherpad-apikey
      - file: etherpad-settings
{%- endif %}

{# Configuration -#}
etherpad-apikey:
  file.managed:
    - name: {{ etherpadLocation }}/APIKEY.txt
    - contents: {{ etherpadSettings['apikey'] }}
    - mode: 600
    - user: etherpad
    - group: etherpad
    - require_in:
        - file: circus-add-watcher-etherpad

etherpad-settings:
  file.managed:
    - name: {{ etherpadLocation }}/settings.json
    - source: salt://makina-states/files/home/etherpad/settings.json
    - template: jinja
    - mode: 600
    - defaults: {{ etherpadSettings|yaml }}
    - user: etherpad
    - group: etherpad
    - require_in:
        - file: circus-add-watcher-etherpad

{#- Run #}
{% import "makina-states/services/monitoring/circus-standalone.sls" as circus with context %}
{{ circus.do(full=full) }}
{{ circus.circusAddWatcher("etherpad", etherpadLocation +"/bin/run.sh") }}

{% endmacro %}
{{ do(full=False) }}
