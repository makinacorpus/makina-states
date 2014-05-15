include:
  - makina-states.cloud.generic.hooks.common
  - makina-states.cloud.generic.hooks.controller
  {% if salt['mc_services.registry']().is['dns.bind'] %}
  - makina-states.services.dns.bind
  {% endif %}

saltcloud-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - sshpass
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:
      - mc_proxy: cloud-generic-controller-pre-pre-deploy
