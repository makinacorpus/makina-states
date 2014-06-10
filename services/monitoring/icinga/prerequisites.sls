{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set icingaSettings = salt['mc_icinga.settings']() %}
include:
  - makina-states.services.monitoring.icinga.hooks

icinga-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      - {{ icingaSettings.package }}

{% if icingaSettings.modules.ido2db.enabled %}
icinga-ido2db-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      - {{ icingaSettings.modules.ido2db.package }}
{% endif %}
