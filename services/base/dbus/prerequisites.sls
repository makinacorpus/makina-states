{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_dbus.settings']() %}
include:
  - makina-states.services.proxy.dbus.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
dbus-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.packages}}
    - watch:
      - mc_proxy: dbus-preinstall
    - watch_in:
      - mc_proxy: dbus-postinstall
{% endif %}
