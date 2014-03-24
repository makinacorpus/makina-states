include:
  - makina-states.cloud.lxc.controller.post-deploy.crons
makina-states-cloud-lxc-controller-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-controller-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-deploy
