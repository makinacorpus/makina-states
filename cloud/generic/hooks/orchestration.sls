include:
  - makina-states.cloud.generic.hooks.common
  - makina-states.cloud.generic.hooks.vm
  - makina-states.cloud.generic.hooks.compute_node
  - makina-states.cloud.generic.hooks.controller

cloud-generic-controller-pre-orch:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:
      - mc_proxy: cloud-generic-controller-pre-pre-deploy
      - mc_proxy: cloud-generic-controller-post-orch

cloud-generic-controller-post-orch:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
      - mc_proxy: cloud-generic-controller-final
    - watch_in:
      - mc_proxy: cloud-generic-final

cloud-generic-compute_node-pre-orch:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
      - mc_proxy: cloud-generic-controller-post-orch
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-orch

cloud-generic-compute_node-post-orch:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
      - mc_proxy: cloud-generic-controller-final
      - mc_proxy: cloud-generic-compute_node-final
    - watch_in:
      - mc_proxy: cloud-generic-final

cloud-generic-vm-pre-orch:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-controller-post-orch
      - mc_proxy: cloud-generic-pre
      - mc_proxy: cloud-generic-compute_node-post-orch
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-pre-deploy

cloud-generic-vm-post-orch:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-pre-orch
      - mc_proxy: cloud-generic-pre
      - mc_proxy: cloud-generic-vm-final
    - watch_in:
      - mc_proxy: cloud-generic-final

