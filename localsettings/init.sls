{#-
# Settings and local configuration to apply to a minion,
# see:
#   - makina-states/doc/ref/formulaes/localsettings/git.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.autoinclude'](localsettings.registry) }}
