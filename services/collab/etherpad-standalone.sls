{#-
# Install in full mode, see the standalone file !
#}
{#-
# Etherpad server
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


{%- if full %}
{#- Download and install etherpad #}
etherpad-install-pkg:
  archive.extracted:
    - name: {{ etherpadSettings['location'] }}
    - source: https://github.com/ether/etherpad-lite/archive/{{ etherpadSettings['version'] }}.zip
    - archive_format: zip
{%- endif %}

{# Configuration -#}
etherpad-apikey:
  file.managed:
    - name: {{ etherpadSettings['location'] }}/APIKEY.txt
    - contents: {{ etherpadSettings['apikey'] }}
    - mode: 600

etherpad-settings:
file.managed:
    - name: {{ etherpadSettings['location'] }}/settings.json
    - source: salt://makina-states/files/
    - mode: 600
    - context:
        title: {{ etherpadSettings['title'] }}
        ip: {{ etherpadSettings['ip'] }}
        port: {{ etherpadSettings['port'] }}
        dbType: {{ etherpadSettings['dbType'] }}
        dbSettings: {{ etherpadSettings['dbSettings'] }}
        requireSession: {{ etherpadSettings['requireSession'] }}
        editOnly: {{ etherpadSettings['editOnly'] }}
        admin: {{ etherpadSettings['admin'] }}
        adminPassword: {{ etherpadSettings['adminPassword'] }}

{#- Run #}
{# Use ./bin/run.sh #}

{% endmacro %}
{{ do(full=False) }}
