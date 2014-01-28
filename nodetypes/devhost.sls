{#-
# Flag the machine as a development box
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'devhost') }}

include:
 - makina-states.nodetypes.vm
 - makina-states.services.mail.postfix
 {% if not 'dockercontainer' in nodetypes.registry['actives'] -%}
 - makina-states.services.mail.dovecot
 {% endif %}
 - makina-states.localsettings.hosts

