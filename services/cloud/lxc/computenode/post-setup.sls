{% set lxcSettings = services.lxcSettings %}
include:
  - makina-states.services.cloud.computenode
etc-init.d-lxc-net-makina:
  file.managed:
    - name: /etc/init.d/lxc-net-makina
    - template: jinja
    - defaults: {{lxcSettings.defaults|yaml}}
    - source: salt://makina-states/files/etc/init.d/lxc-net-makina.sh
    - mode: 750
    - user: root
    - group: root
    - require_in:
      - service: lxc-services-enabling
{% endif %}

{% if grains['os'] in ['Ubuntu'] %}
etc-init-lxc-net-makina:
  file.managed:
    - name: /etc/init/lxc-net-makina.conf
    - template: jinja
    - source: salt://makina-states/files/etc/init/lxc-net-makina.conf
    - mode: 750
    - user: root
    - defaults: {{lxcSettings.defaults|yaml}}
    - group: root
    - require_in:
      - service: lxc-services-enabling
