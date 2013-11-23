#
# Configure machine physical network based on pillar information
#
# The template is shared with the lxc state, please also look it
#
# *-makina-network:
#   ifname:
#   - auto: (opt) (default: True)
#   - mode: (opt) (default: dhcp or static if address)
#   - address: (opt)
#   - netmask: (opt)
#   - gateway: (opt)
#   - dnsservers: (opt)
#
# EG:
# myhost-makina-network:
#   etho: # manually configured interface
#     - address: 8.1.5.4
#     - netmask: 255.255.255.0
#     - gateway: 8.1.5.1
#     - dnsservers: 8.8.8.8
#   em1: {} # -> dhcp based interface

{% if grains['os_family'] in ['Debian'] %}
network-cfg:
  file.managed:
    - name: /etc/network/interfaces
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - name: /etc/network/interfaces
    - source: salt://makina-states/files/etc/network/interfaces
    - makina_network: {}
# tradeof to make the lxc state work with us


network-services:
  service.running:
    - enable: True
    - names:
      - networking
      - resolvconf
    - watch:
      - file: network-cfg
{% endif %}
