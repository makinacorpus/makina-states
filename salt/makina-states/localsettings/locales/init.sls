{#-
# locales managment
# see:
#   - makina-states/doc/ref/formulaes/localsettings/locales.rst
#}
{{ salt['mc_macros.register']('localsettings', 'locales') }}
include:
  - makina-states.localsettings.locales.prerequisites
  - makina-states.localsettings.locales.configuration

