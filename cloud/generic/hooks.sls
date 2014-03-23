cloud-generic-pre-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-post-post-deploy
      - mc_proxy: cloud-generic-post-pre-deploy
      - mc_proxy: cloud-generic-post-deploy
      - mc_proxy: cloud-generic-pre-post-deploy
      - mc_proxy: cloud-generic-pre-deploy
      - mc_proxy: cloud-generic-final

cloud-generic-pre-reverseproxy-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre-pre-deploy
    - watch_in:
      - mc_proxy: cloud-post-reverseproxy-deploy

cloud-post-reverseproxy-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-pre-post-deploy

cloud-generic-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-post-deploy
      - mc_proxy: cloud-generic-pre-deploy
      - mc_proxy: cloud-generic-pre-post-deploy
      - mc_proxy: cloud-generic-final
      - mc_proxy: cloud-generic-post-post-deploy

cloud-generic-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-pre-post-deploy
      - mc_proxy: cloud-generic-post-deploy
      - mc_proxy: cloud-generic-post-post-deploy
      - mc_proxy: cloud-generic-final

cloud-generic-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-pre-post-deploy
      - mc_proxy: cloud-generic-post-post-deploy
      - mc_proxy: cloud-generic-final

cloud-generic-pre-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-post-post-deploy
      - mc_proxy: cloud-generic-final

cloud-generic-post-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-final

cloud-generic-final:
  mc_proxy.hook: []
