{#-
# RVM integration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/timezone.rst

#}
include:
  - makina-states.localsettings.timezone.hooks
{% set data = salt['mc_timezone.settings']() %}
{% if data.tz %}
tz-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{data.pkgs}}
    - watch:
      - mc_proxy: timezone-pre-inst
    - watch_in:
      - mc_proxy: timezone-post-inst
{% endif %}
