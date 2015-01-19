include:
  - makina-states.cloud.generic.hooks

cloud-saltify-pre-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:
      - mc_proxy: cloud-saltify-post-pre-deploy
      - mc_proxy: cloud-saltify-post-post-deploy
      - mc_proxy: cloud-saltify-pre-post-deploy
      - mc_proxy: cloud-saltify-post-deploy
      - mc_proxy: cloud-saltify-pre-deploy

cloud-saltify-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-saltify-post-post-deploy
      - mc_proxy: cloud-saltify-pre-post-deploy
      - mc_proxy: cloud-saltify-post-deploy
      - mc_proxy: cloud-saltify-pre-deploy

cloud-saltify-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-saltify-post-post-deploy
      - mc_proxy: cloud-saltify-pre-post-deploy
      - mc_proxy: cloud-saltify-post-deploy

cloud-saltify-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-saltify-pre-post-deploy
      - mc_proxy: cloud-saltify-post-post-deploy

cloud-saltify-pre-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-saltify-post-post-deploy

cloud-saltify-post-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-final

