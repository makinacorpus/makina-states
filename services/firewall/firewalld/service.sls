include:
  - makina-states.services.firewall.firewalld.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.localsettings.network
firewalld-disable-makinastates-shorewall:
  file.absent:
    - names:
      - /etc/rc.local.d/shorewall.sh
    - watch:
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart

firewalld-conflicting-services:
  service.dead:
    - names: [iptables, ebtables, shorewall, shorewall6]
    - enabled: false
    - watch:
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
firewalld:
  service.running:
    - enabled: true
    - names:
      - firewalld
    - watch:
      - service: firewalld-ebtables
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
{%endif %}
