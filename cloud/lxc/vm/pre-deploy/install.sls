include:
  - makina-states.cloud.generic.hooks.vm
makina-states-cloud-lxc-vm-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-pre-deploy
