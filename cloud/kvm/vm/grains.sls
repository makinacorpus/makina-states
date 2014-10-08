run-grains-b:
  mc_registry.update:
    - name: nodetypes
    - params: {kvmcontainer: true}
lxc-run-grains:
  mc_registry.update:
    - name: cloud
    - params:
        is.vm: true
        is.lvmvm: true
