include:
  - makina-states.localsettings.locales.hooks

{% set data = salt['mc_locales.settings']() %}
locales-pkg:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{data.packages}}
    - watch_in:
      - mc_proxy: locales-post-inst
