{%- import "makina-states/localsettings/rvm/macros.jinja" as rvmmac %}
{{ salt['mc_macros.register']('localsettings', 'rvm') }}
include:
 - makina-states.localsettings.rvm.hooks
 - makina-states.localsettings.rvm.prerequisites
 - makina-states.localsettings.rvm.configuration 
{% set install_ruby = rvmmac.install_ruby %}
{% set rvm = rvmmac.rvm %}
{% set rvm_env = rvmmac.rvm_env %}
