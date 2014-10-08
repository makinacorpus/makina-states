include:
  - makina-states.services.virt.kvm.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
kvm-services-enabling:
  service.running:
    - reload: true
    - enable: true
    - names:
      - libvirt-bin
    - watch:
      - mc_proxy: kvm-pre-restart
    - watch_in:
      - mc_proxy: kvm-post-inst
{% endif %}
