{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_dbus.settings']() %}
include:
  - makina-states.services.base.dbus.hooks
dbus-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.packages}}
    - watch:
      - mc_proxy: dbus-preinstall
    - watch_in:
      - mc_proxy: dbus-postinstall
