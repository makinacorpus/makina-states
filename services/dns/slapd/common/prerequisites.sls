{% if salt['mc_controllers.mastersalt_mode']() %}
{% set settings = salt['mc_slapd.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %} 
include:
  - makina-states.services.dns.slapd.hooks
slapd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: slapd-pre-install
    - watch_in:
      - mc_proxy: slapd-post-install
{% endif %}
