include:
  - makina-states.cloud.generic.hooks.compute_node
makina-states-cloud-lxc-compute_node-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy
