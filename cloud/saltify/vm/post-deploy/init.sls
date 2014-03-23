include:
  - makina-states.cloud.saltify.hooks

cloud-saltify-not-applicable-vm-post-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-saltify-pre-post-deploy
    - watch_in:
      - mc_proxy: cloud-saltify-post-post-deploy
