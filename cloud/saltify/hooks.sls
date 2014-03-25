include:
  - makina-states.cloud.generic.hooks.common
  - makina-states.cloud.generic.hooks.compute_node

cloud-saltify-pre-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-pre-deploy
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
      - mc_proxy: cloud-generic-compute_node-pre-deploy
      - mc_proxy: cloud-generic-compute_node-pre-reverseproxy-deploy
      - mc_proxy: cloud-generic-compute_node-pre-grains-deploy

