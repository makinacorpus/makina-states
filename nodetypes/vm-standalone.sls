{#
# separate file to to the vagrant vm setup, to be reused in other states
# while not reimporting the whole makina-states stack.
#} 
{#-
#
# Extra setup for a virtual machine running on a bare metal server
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'vm') }}
