
include:
  - makina-states.services.firewall.shorewall
  - makina-states.services.virt.lxc
{% if grains['os'] not in ['Ubuntu'] %}
etc-init.d-lxc-net-makina:
  file.managed:
    - name: /etc/init.d/lxc-net-makina
    - template: jinja
    - source: salt://makina-states/files/etc/init.d/lxc-net-makina.sh
    - mode: 750
    - user: root
    - group: root
    - watch_in:
      - mc_proxy: lxc-post-conf
{% else %}
etc-init-lxc-net-makina:
  file.managed:
    - name: /etc/init/lxc-net-makina.conf
    - template: jinja
    - source: salt://makina-states/files/etc/init/lxc-net-makina.conf
    - mode: 750
    - user: root
    - group: root
    - watch_in:
      - mc_proxy: lxc-post-conf
{% endif %}
lxc-makina-services-enabling:
  service.running:
    - enable: True
    - names:
      - lxc
      - lxc-net
      - lxc-net-makina
    - require_in:
      - mc_proxy: lxc-post-inst
