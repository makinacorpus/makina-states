{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/java/tomcat7-standalone.sls" as base with context %}
{{base.do(full=True)}}
