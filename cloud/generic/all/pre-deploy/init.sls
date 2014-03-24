include:
  - makina-states.cloud.generic.hooks

cloud-generic-not-applicable-all-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-post-pre-deploy
