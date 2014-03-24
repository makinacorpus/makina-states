include:
  - makina-states.cloud.generic.hooks.controller

cloud-generic-not-applicable-controller-post-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-controller-pre-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-post-deploy
