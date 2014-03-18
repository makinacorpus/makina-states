{#
# Flag this machine as a lxc container
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/travis.rst
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'travis') }}
{% set localsettings = nodetypes.localsettings %}
{% if full %}
include:
  - makina-states.nodetypes.devhost
{% endif %}
{% endmacro %}
{{do(full=False)}}
