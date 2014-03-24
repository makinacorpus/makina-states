cloud-generic-compute_node-pre-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-pre-deploy

cloud-generic-compute_node-post-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-deploy

cloud-generic-compute_node-pre-grains-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-post-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-grains-deploy

cloud-generic-compute_node-post-grains-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-deploy

cloud-generic-compute_node-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy

cloud-generic-compute_node-pre-firewall-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-firewall-deploy

cloud-generic-compute_node-post-firewall-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy
      - mc_proxy: cloud-generic-compute_node-pre-reverseproxy-deploy

cloud-generic-compute_node-pre-reverseproxy-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-reverseproxy-deploy

cloud-generic-compute_node-post-reverseproxy-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy

cloud-generic-compute_node-pre-virt-type-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-post-reverseproxy-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-virt-type-deploy

cloud-generic-compute_node-post-virt-type-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy

cloud-generic-compute_node-pre-images-deploy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-compute_node-post-virt-type-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-images-deploy

cloud-generic-compute_node-post-images-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy

cloud-generic-compute_node-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-post-deploy

cloud-generic-compute_node-pre-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-final

cloud-generic-compute_node-post-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-final

cloud-generic-compute_node-final:
  mc_proxy.hook: []

