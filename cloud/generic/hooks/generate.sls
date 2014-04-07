cloud-generic-generate:
  mc_proxy.hook:
    - require_in: 
      - mc_proxy: cloud-generic-generate-end
cloud-generic-generate-end:
  mc_proxy.hook: []

