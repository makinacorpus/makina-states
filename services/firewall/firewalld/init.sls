{{ salt['mc_macros.register']('services', 'firewall.firewalld') }}

include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.docker.hooks
  - makina-states.services.firewall.firewalld.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.localsettings.network
  - makina-states.localsettings.localrc
  - makina-states.services.firewall.firewalld.prerequisites
  - makina-states.services.firewall.firewalld.configuration
  - makina-states.services.firewall.firewalld.service
{% endif %}
firewalld-orchestrate:
  mc_proxy.hook:
    - watch:
      - file: rc-local-d
      - mc_proxy: lxc-post-inst
      - mc_proxy: docker-post-inst
    - watch_in:
      - mc_proxy: firewalld-preconf
