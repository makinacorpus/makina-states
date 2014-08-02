{#
# Flag this machine as a lxc container
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/travis.rst
#}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'travis') }}
{% if full %}
include:
  - makina-states.nodetypes.devhost
{% endif %}
{% endmacro %}
{{do(full=False)}}
