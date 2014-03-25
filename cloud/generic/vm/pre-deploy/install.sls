include:
  - makina-states.cloud.generic.hooks

cloud-generic-not-applicable-vm-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-pre-deploy
