{#
# Flag this machine as a lxc container
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/dockercontainer.rst
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'dockercontainer') }}
{% if full %}
include:
  - makina-states.nodetypes.lxccontainer
{% endif %}
{% endmacro %}
{{do(full=False)}}
