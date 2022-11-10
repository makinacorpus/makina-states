{# do not do any configuration, use Host as-is #}
{% import "makina-states/nodetypes/scratch-standalone.sls" as base with context %}
{{base.do(full=True)}}
