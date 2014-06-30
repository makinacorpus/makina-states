{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set mumbleSettings = salt['mc_mumble.settings']() %}
include:
  - makina-states.services.sound.mumble.hooks

mumble-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - mumble-server
    - watch:
      - mc_proxy: mumble-pre-install-hook
    - watch_in:
      - mc_proxy: mumble-pre-hardrestart-hook
      - mc_proxy: mumble-post-install-hook

