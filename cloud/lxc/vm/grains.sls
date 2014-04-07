run-grains-b:
  mc_registry.update:
    - name: nodetypes
    - params: {lxccontainer: true}
lxc-run-grains:
  mc_registry.update:
    - name: cloud
    - params:
      is.vm: true
      is.lxcvm: true
