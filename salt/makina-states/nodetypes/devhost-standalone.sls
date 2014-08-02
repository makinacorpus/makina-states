{#-
# Flag the machine as a development box
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/devhost.rst
#}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'devhost') }}
include:
  {% if salt['mc_nodetypes.is_devhost']() %}
  - makina-states.services.mail.postfix
  - makina-states.services.mail.dovecot
  {% endif %}
  - makina-states.localsettings.hosts
  {% if full %}
  - makina-states.nodetypes.vm
  {% endif %}
{% endmacro %}
{{do(full=False)}}
