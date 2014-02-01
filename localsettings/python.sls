{#- Install in full mode, see the standalone file !  #}
{% import  "makina-states/localsettings/python-standalone.sls" as base with context %}
{{base.do(full=True)}}
