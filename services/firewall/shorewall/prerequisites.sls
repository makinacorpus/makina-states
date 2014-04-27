include:
  - makina-states.services.firewall.shorewall.hooks

{% if salt['mc_controllers.mastersalt_mode']() %}
shorewall-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - shorewall6
      - shorewall
    - require_in:
      - mc_proxy: shorewall-postinstall
{% endif %}
