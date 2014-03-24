cloud-generic-vm-pre-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-pre-deploy


cloud-generic-vm-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-deploy

cloud-generic-vm-pre-grains-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-vm-post-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-grains-deploy

cloud-generic-vm-post-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-deploy

cloud-generic-vm-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-deploy

cloud-generic-vm-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-pre-post-deploy

cloud-generic-vm-pre-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-post-deploy

cloud-generic-vm-post-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-vm-final

cloud-generic-vm-final:
  mc_proxy.hook: []
