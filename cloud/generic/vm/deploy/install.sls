include:
  - makina-states.cloud.generic.hooks

cloud-generic-not-applicable-vm-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-deploy
