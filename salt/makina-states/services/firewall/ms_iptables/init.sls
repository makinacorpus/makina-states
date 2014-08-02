include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.docker.hooks
  - makina-states.services.firewall.ms_iptables.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% if salt['mc_services.registry']()['has'].get('virt.lxc') %}
# restart bridge upon install
  - makina-states.services.virt.lxc.services
{% endif %}
  - makina-states.services.firewall.shorewall.disable
  - makina-states.services.firewall.firewalld.disable
  - makina-states.localsettings.network
  - makina-states.services.firewall.ms_iptables.prerequisites
  - makina-states.services.firewall.ms_iptables.configuration
  - makina-states.services.firewall.ms_iptables.services
{% endif %}
ms_iptables-orchestrate:
  mc_proxy.hook:
    - watch:
      - mc_proxy: lxc-post-inst
      - mc_proxy: docker-post-inst
    - watch_in:
      - mc_proxy: ms_iptables-preconf
