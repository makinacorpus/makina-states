kvm-pre-pkg:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: kvm-pre-conf
      - mc_proxy: kvm-post-conf
      - mc_proxy: kvm-post-pkg
      - mc_proxy: kvm-pre-restart
      - mc_proxy: kvm-post-inst

kvm-post-pkg:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: kvm-pre-conf
      - mc_proxy: kvm-post-conf
      - mc_proxy: kvm-pre-restart
      - mc_proxy: kvm-post-inst

kvm-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: kvm-post-conf
      - mc_proxy: kvm-pre-restart
      - mc_proxy: kvm-post-inst

kvm-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: kvm-pre-restart
      - mc_proxy: kvm-post-inst

kvm-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: kvm-post-inst

kvm-post-inst:
  mc_proxy.hook: []
