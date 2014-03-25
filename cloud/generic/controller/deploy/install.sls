include:
  - makina-states.cloud.generic.hooks.controller

cloud-generic-not-applicable-controller-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-controller-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-deploy
