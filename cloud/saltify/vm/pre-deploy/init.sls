include:
  - makina-states.cloud.saltify.hooks

cloud-saltify-not-applicable-vm-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-saltify-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-saltify-post-pre-deploy
