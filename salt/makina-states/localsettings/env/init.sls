{#-
# pamldap configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/ldap.rst
#}

{{ salt['mc_macros.register']('localsettings', 'env') }}
# the magic is here, calling env  write the localreg
{% set settings = salt['mc_env.settings']() %}
include:
  - makina-states.localsettings.env.hooks

