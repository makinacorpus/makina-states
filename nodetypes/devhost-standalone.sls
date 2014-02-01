{#
# separate file to to the vagrant vm setup, to be reused in other states
# while not reimporting the whole makina-states stack.
#}
{#-
#
# Flag the machine as a development box
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'devhost') }}
include:
  {% if nodetypes.registry.is.devhost %}
  - makina-states.services.mail.postfix
  - makina-states.services.mail.dovecot
  {% endif %}
  - makina-states.localsettings.hosts
  {% if full %}
  - makina-states.nodetypes.vm
  {% endif %}
{% endmacro %}
{{do(full=False)}}
