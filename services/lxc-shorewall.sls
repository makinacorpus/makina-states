#
# LXC and shorewall integration, be sure to add
# lxc guests to shorewall running state
# upon creation
# A big sentence to say, restart shorewall
# after each lxc creation to enable
# the container network
#
include:
  - makina-states.services.shorewall
  - makina-states.services.lxc

extend:
  {%- for k, lxc_data in pillar.items() %}
  {% if k.endswith('lxc-server-def')  -%}
  {% set lxc_name = lxc_data.get('name', k.split('-lxc-server-def')[0]) -%}
  {% set lxc_mac = lxc_data['mac'] -%}
  {% set lxc_ip4 = lxc_data['ip4'] -%}
  {% set lxc_template = lxc_data.get('template', 'ubuntu') -%}
  {% set lxc_netmask = lxc_data.get('netmask', '255.255.255.0') -%}
  {% set lxc_gateway = lxc_data.get('gateway', '10.0.3.1') -%}
  {% set lxc_dnsservers = lxc_data.get('dnsservers', '10.0.3.1') -%}
  {% set lxc_root = lxc_data.get('root', '/var/lib/lxc/' + lxc_name) -%}
  {% set lxc_rootfs = lxc_data.get('rootfs', lxc_root + '/rootfs') -%}
  {% set lxc_config = lxc_data.get('config', lxc_root + '/config') -%}
  start-{{ lxc_name }}-lxc-service:
    cmd.run:
      - watch_in:
        - cmd: shorewall-restart
  {% endif %}
{% endfor -%}
