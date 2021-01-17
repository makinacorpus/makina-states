include:
  - makina-states.services.virt.kvm.hooks
kvm-services-enabling:
  service.running:
    - reload: true
    - enable: true
    - names:
      {% if salt['mc_utils.loose_version'](grains.get('osrelease', '')) >= salt['mc_utils.loose_version']('20.04') %}
      - libvirtd.service
      - libvirt-guests.service
      {% else %}
      libvirt-bin
      {% endif %}
    - watch:
      - mc_proxy: kvm-pre-restart
    - watch_in:
      - mc_proxy: kvm-post-inst
