run-grains:
  mc_registry.update:
    - name: cloud
    - params:
        is.lxchost: true
run-grains-b:
  mc_registry.update:
    - name: services
    - params:
        virt.lxc: true
