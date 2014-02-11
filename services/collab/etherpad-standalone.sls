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

{%- if full %}
{#- Remove directory if exists, else archive won't extract #}
etherpad-delete-old:
  file.absent:
    - name: {{ etherpadSettings['location'] }}

{#- Download and install etherpad #}
etherpad-install-pkg:
  archive.extracted:
    - name: {{ etherpadSettings['location'] }}
    - source: https://github.com/ether/etherpad-lite/archive/{{ etherpadSettings['version'] }}.zip
    - source_hash: sha256=d71ba3127ab8902f9b2cc3d706e07357ea0764c3fd901204bcad1fa310e7772b
    - archive_format: zip
{%- endif %}

{# Configuration -#}
etherpad-apikey:
  file.managed:
    - name: {{ etherpadLocation }}/APIKEY.txt
    - contents: {{ etherpadSettings['apikey'] }}
    - mode: 600

etherpad-settings:
  file.managed:
    - name: {{ etherpadLocation }}/settings.json
    - source: salt://makina-states/files/home/etherpad/settings.json
    - mode: 600
    - defaults: {{ etherpadSettings|yaml }}

{#- Run #}
{% import "makina-states/services/monitoring/circus-standalone.sls" as circus with context %}
{{ circus.do(full=True) }}
{{ circus.circusAddWatcher("etherpad", etherpadLocation +"/bin/run.sh") }}

{% endmacro %}
{{ do(full=False) }}
