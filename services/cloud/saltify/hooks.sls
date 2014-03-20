include:
  - makina-states.services.cloud.cloudcontroller.hooks
saltify-pre-install:
  mc_proxy.hook:
    - watch:
      - mc_proxy: salt-cloud-postinstall
    - watch_in:
      - mc_proxy: saltify-post-install
saltify-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: saltify-pre-deploy
saltify-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: saltify-post-deploy
saltify-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: salt-cloud-postdeploy
