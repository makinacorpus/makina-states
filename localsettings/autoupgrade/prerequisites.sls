include:
  - makina-states.localsettings.pkgs-hooks
{% if grains['os'] in ['Ubuntu'] %}
{% if salt['mc_controllers.mastersalt_mode']() %}
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
{%endif %}
