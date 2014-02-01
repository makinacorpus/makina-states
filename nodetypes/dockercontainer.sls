{# Makina-states autodiscovery integration file #}
{% import "makina-states/nodetypes/dockercontainer-standalone.sls" as base with context %}
{{base.do(full=True)}}
