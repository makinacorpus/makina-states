include:
  - makina-states.localsettings.autoupgrade.hooks
{% if grains['os_family'] in ['Debian'] %}
{%- set data = salt['mc_autoupgrade.settings']() %}
unattended-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - unattended-upgrades
    - watch_in:
      - mc_proxy: after-au-pkg-install-proxy
    - watch:
      - mc_proxy: before-au-pkg-install-proxy
{%endif %}
