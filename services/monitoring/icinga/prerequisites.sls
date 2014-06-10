{% set pkgssettings = salt['mc_pkgs.settings']() %}
{%- set icingaSettings = salt['mc_icinga.settings']() %}
{%- set venv = icingaSettings['location'] + "/venv" %}
include:
  - makina-states.services.monitoring.icinga.hooks

icinga-pkgs:
  pkg.{{pkgsettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install-hook
    - watch_in:
      - mc_proxy: icinga-post-install-hook
    - pkgs:
      - {{ icingaSettings.package }}

{% if icingaSettings.modules.ido2db.enabled %}
icinga-ido2db-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install-hook # TODO: execute after icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install-hook
    - pkgs:
      - {{ icingaSettings.modules.ido2db.package }}
{% endif %}
