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

{% if full %}
include:
  - makina-states.localsettings.nodejs
  - makina-states.services.monitoring.circus
{% else %}
include:
  - makina-states.localsettings.nodejs-standalone
  - makina-states.services.monitoring.circus-standalone
{% endif %}

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
  archive.extracted:
    - name: {{ etherpadSettings['location'] }}
    - archive_format: zip
    - if_missing: {{ etherpadSettings['location']}}/etherpad-lite-{{etherpadSettings['version']}}/var
    - source: https://github.com/ether/etherpad-lite/archive/{{ etherpadSettings['version'] }}.zip
    - source_hash: md5=af569ee46c7e14c84002aa7a8d6d29bd
    - require:
      - user: etherpad
      - file: etherpad-create-directory
  cmd.run:
    - name: chown -Rf etherpad:etherpad {{ etherpadSettings['location'] }}
    - require:
      - archive: etherpad-install-pkg
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
{{ circus.circusAddWatcher("etherpad", etherpadLocation +"/bin/run.sh") }}

{% endmacro %}
{{ do(full=False) }}
