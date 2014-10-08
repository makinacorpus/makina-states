run-grains:
  mc_registry.update:
    - name: cloud
    - params:
        is.kvmhost: true
run-grains-b:
  mc_registry.update:
    - name: services
    - params:
        virt.kvm: true
