{% set data = salt['mc_firewalld.settings']() %}
include:
  - makina-states.services.firewall.shorewall.disable
  - makina-states.services.firewall.firewalld.hooks
  - makina-states.services.firewall.firewall.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.localsettings.network
  - makina-states.services.firewall.firewall.configuration
firewalld-conflicting-services:
  service.dead:
    - names: [iptables, ebtables,
              shorewall, shorewall6]
    - enable: false
    - watch:
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
{% if data.get('permissive_mode', False) %}
firewalld:
  service.dead:
    - enable: false
    - names:
      - firewalld
      - polkitd
    - require:
      - mc_proxy: firewalld-prerestart
      - service: firewalld-conflicting-services
    - require_in:
      - mc_proxy: firewalld-postrestart
  {# polkit in container world is evil ! #}
  {% if  salt['mc_nodetypes.is_container']() %}
  file.symlink:
    - name: /etc/systemd/system/polkitd.service
    - target: /dev/null
    - onlyif: test -e /lib/systemd/system/polkitd.service
    - require:
      - mc_proxy: firewalld-prerestart
      - service: firewalld-conflicting-services
    - require_in:
      - mc_proxy: firewalld-postrestart
  {% else %}
  file.absent:
    - name: /etc/systemd/system/polkitd.service
    - onlyif: >
              test -h /etc/systemd/system/polkitd.service &&
              test "x$(readlink /etc/systemd/system/polkitd.service)" = "x/dev/null"
    - require:
      - mc_proxy: firewalld-prerestart
      - service: firewalld-conflicting-services
    - require_in:
      - mc_proxy: firewalld-postrestart
  {% endif %}
firewalld-reapply:
  cmd.run:
    - name: /bin/true
    - onlyif: /bin/false
    - watch:
      - service: firewalld
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
firewalld-disable-firewall:
  cmd.run:
    - name: /usr/bin/ms_disable_firewall.sh fromsalt nohard
    - stateful: true
    - watch:
      - service: firewalld
      - mc_proxy: firewall-postconf
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
{%else %}
firewalld:
  service.running:
    - enable: true
    - names:
      - firewalld
    - require:
      - service: firewalld-conflicting-services
      - mc_proxy: firewalld-prerestart
    - require_in:
      - mc_proxy: firewalld-postrestart
firewalld-reapply:
  cmd.run:
    - name: /usr/bin/ms_firewalld.py --fromsalt
    - stateful: true
    - watch:
      - service: firewalld
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
{%endif %}
{%endif %}
