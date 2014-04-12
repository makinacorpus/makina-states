{% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.localsettings.locales.hooks

locales-pkg:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - locales
    - watch_in:
      - mc_proxy: locales-post-inst
