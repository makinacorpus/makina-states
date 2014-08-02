{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set settings = salt['mc_bind.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %} 
include:
  - makina-states.services.dns.bind.hooks
bind-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: bind-pre-install
    - watch_in:
      - mc_proxy: bind-post-install
{% endif %}
