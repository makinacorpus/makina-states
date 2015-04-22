{#-
# Flag the machine as a development box
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/vm.rst
#}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'vm') }}
{% if full %}
include:
  - makina-states.nodetypes.server
{% endif %}

makinastates-snapshot.sh:
  file.managed:
    - name: /sbin/makinastates-snapshot.sh
    - source: salt://makina-states/files/sbin/makinastates-snapshot.sh
    - user: root
    - group: root
    - mode: 0755
{% endmacro %}
{{do(full=False)}}
