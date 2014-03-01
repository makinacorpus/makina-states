{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/cloud/salt_cloud-standalone.sls" as base with context %}
{{base.do(full=True)}}
