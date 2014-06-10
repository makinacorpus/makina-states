{%- set icingaSettings = salt['mc_icinga.settings']() %}
{%- set venv = icingaSettings['location'] + "/venv" %}
include:
  - makina-states.services.monitoring.icinga.hooks

icinga-pkgs:
  pkg.{{icingaSettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install-hook
    - watch_in:
      - mc_proxy: icinga-post-install-hook
    - pkgs:
      - {{ salt['mc_icinga.settings']().package }}

{% if salt['mc_icinga.settings']().modules.ido2db.enabled %}
icinga-ido2db-pkgs:
    - watch:
      - mc_proxy: icinga-pre-install-hook
    - watch_in:
      - mc_proxy: icinga-post-install-hook
    - pkgs:
      - {{ salt['mc_icinga.settings']().modules.ido2db.package }}
{% endif %}
