include:
  - makina-states.cloud.generic.hooks

cloud-generic-not-applicable-all-setup:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-post-deploy
