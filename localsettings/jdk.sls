{#- Install in full mode, see the standalone file !  #}
{% import  "makina-states/localsettings/jdk-standalone.sls" as base with context %}
{{base.do(full=True)}}
