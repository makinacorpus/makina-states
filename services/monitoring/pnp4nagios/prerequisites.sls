{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set pnp4nagiosSettings = salt['mc_pnp4nagios.settings']() %}
include:
  - makina-states.services.monitoring.pnp4nagios.hooks

pnp4nagios-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: pnp4nagios-pre-install
    - watch_in:
      - mc_proxy: pnp4nagios-post-install
    - pkgs:
      {% for package in pnp4nagiosSettings.package %}
      - {{package}}
      {% endfor %}


# it nagios3 may be a dependency for pnp4nagios (in the unbuntu package)

