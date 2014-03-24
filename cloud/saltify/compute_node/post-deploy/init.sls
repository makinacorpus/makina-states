include:
  - makina-states.cloud.saltify.hooks

cloud-saltify-not-applicable-compute_node-setup:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-saltify-pre-deploy
    - watch_in:
      - mc_proxy: cloud-saltify-post-deploy
