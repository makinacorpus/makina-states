{#-
# Settings and local configuration to apply to a minion,
# see:
#   - makina-states/doc/ref/formulaes/localsettings/git.rst
#}
{{ salt['mc_macros.autoinclude'](salt['mc_localsettings.registry']()) }}
