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

disable-apache2-sa:
  service.disabled:
    - names:
      - apache2
      - nagios3
    - watch:
      - pkg: pnp4nagios-pkgs
      - mc_proxy: pnp4nagios-pre-install
    - watch_in:
      - mc_proxy: pnp4nagios-post-install
disable-apache2-sd:
  service.dead:
    - names:
      - apache2
      - nagios3
    - enable: False
    - watch:
      - pkg: pnp4nagios-pkgs
      - mc_proxy: pnp4nagios-pre-install
    - watch_in:
      - mc_proxy: pnp4nagios-post-install
# it nagios3 may be a dependency for pnp4nagios (in the unbuntu package)

