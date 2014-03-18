{#- Install in full mode, see the standalone file !  #}
{% import  "makina-states/localsettings/jdk-standalone.sls" as base with context %}
{% set jdk_pkgs = base.jdk_pkgs %}
{{base.do(full=True)}}
