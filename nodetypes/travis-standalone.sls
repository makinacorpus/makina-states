{#
# separate file to to the vagrant vm setup, to be reused in other states
# while not reimporting the whole makina-states stack.
#}
{#
# Flag this machine as a travis node worker
#
# Only nuance for now is to disable sysctls in salt 's macro
#
#}

{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'travis') }}
{% set localsettings = nodetypes.localsettings %}
