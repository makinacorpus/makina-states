{#-
# Makina-states autodiscovery integration file, see the -standalone file
#}
{% import "makina-states/nodetypes/devhost-standalone.sls" as base with context %}
{{base.do(full=True)}}
