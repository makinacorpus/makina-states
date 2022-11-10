network-cfg-gen:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: network-1nd
network-1nd:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: network-2nd
network-2nd:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: network-last-hook
network-last-hook:
  mc_proxy.hook:
    - order: last
