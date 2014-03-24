cloud-generic-pre-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-post-post-deploy
      - mc_proxy: cloud-generic-post-pre-deploy
      - mc_proxy: cloud-generic-post-deploy
      - mc_proxy: cloud-generic-pre-post-deploy
      - mc_proxy: cloud-generic-pre-deploy
      - mc_proxy: cloud-generic-final

cloud-generic-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-post-deploy
      - mc_proxy: cloud-generic-pre-deploy
      - mc_proxy: cloud-generic-pre-post-deploy
      - mc_proxy: cloud-generic-final
      - mc_proxy: cloud-generic-post-post-deploy

cloud-generic-pre-grains-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-post-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-post-grains-deploy

cloud-generic-post-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-pre-deploy
      - mc_proxy: cloud-generic-pre-reverseproxy-deploy

cloud-generic-pre-reverseproxy-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-post-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-post-reverseproxy-deploy

cloud-generic-post-reverseproxy-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-pre-deploy

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
