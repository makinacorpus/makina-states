include:
  - makina-states.cloud.generic.hooks.common

cloud-generic-controller-pre-pre-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:

      - mc_proxy: cloud-generic-controller-post-pre-deploy

cloud-generic-controller-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-controller-pre-deploy

cloud-generic-controller-pre-grains-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-controller-post-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-grains-deploy

cloud-generic-controller-post-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-controller-pre-deploy

cloud-generic-controller-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-deploy

cloud-generic-controller-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-controller-pre-post-deploy

cloud-generic-controller-pre-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-post-deploy

cloud-generic-controller-post-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-controller-final

cloud-generic-controller-final:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-final
