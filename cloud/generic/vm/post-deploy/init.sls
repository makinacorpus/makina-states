include:
  - makina-states.cloud.generic.hooks

cloud-generic-not-applicable-vm-post-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-post-post-deploy
