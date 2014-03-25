include:
  - makina-states.cloud.generic.hooks.compute_node
makina-states-cloud-lxc-compute-post-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-post-deploy
