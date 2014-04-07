{{ salt['mc_macros.register']('services', 'firewall.shorewall') }}

include:
  - makina-states.localsettings.localrc
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.docker-hooks
  - makina-states.services.firewall.shorewall.hooks
  - makina-states.services.firewall.shorewall.prerequisites
  - makina-states.services.firewall.shorewall.configuration
  - makina-states.services.firewall.shorewall.service

shorewall-orchestrate:
  mc_proxy.hook:
    - watch:
      - file: rc-local
      - mc_proxy: lxc-post-inst
      - mc_proxy: docker-post-inst
    - watch_in:
      - mc_proxy: shorewall-preconf
