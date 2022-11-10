{% set settings = salt['mc_shorewall.settings']() %}
include:
  {% if settings.ulogd %}
  - makina-states.services.log.ulogd
  {% endif %}
  - makina-states.services.firewall.shorewall.hooks

shorewall-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
    {% if grains.get('osrelease', '') != '5.0.10' %}
      - shorewall6
    {% endif%}
      - shorewall
    - require_in:
      - mc_proxy: shorewall-postinstall
