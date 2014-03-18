{#-
#  Dummies states for orchestration and reuse
#  in standalone modes
#}
{%- import "makina-states/_macros/controllers.jinja" as controllers with context %}
{%- set saltmac = controllers.saltmac %}
{%- set name = saltmac.saltname %}
{{ saltmac.salt_dummies(name) }}
{{ saltmac.daemon_dummies(name) }}
