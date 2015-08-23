{% set data = salt['mc_ms_iptables.settings']() %}
include:
  - makina-states.services.firewall.shorewall.disable
  - makina-states.services.firewall.firewalld.disable
  - makina-states.services.firewall.ms_iptables.hooks
  - makina-states.services.firewall.firewall.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.localsettings.network
  - makina-states.services.firewall.firewall.configuration
ms_iptables-conflicting-services:
  service.dead:
    - names: [iptables, ebtables, firewalld, shorewall, shorewall6]
    - enable: false
    - watch:
      - mc_proxy: ms_iptables-prerestart
    - watch_in:
      - mc_proxy: ms_iptables-postrestart
{% if data.get('permissive_mode', False) %}
ms_iptables:
  service.dead:
    - enable: false
    - names:
      - ms_iptables
    - require:
      - mc_proxy: ms_iptables-prerestart
      - service: ms_iptables-conflicting-services
    - require_in:
      - mc_proxy: ms_iptables-postrestart
ms_iptables-reapply:
  cmd.run:
    - name: /bin/true
    - onlyif: /bin/false
    - watch:
      - service: ms_iptables
      - mc_proxy: ms_iptables-prerestart
    - watch_in:
      - mc_proxy: ms_iptables-postrestart
ms_iptables-disable-firewall:
  cmd.run:
    - name: /usr/bin/ms_iptables.py --from-salt --stop
    - stateful: true
    - watch:
      - service: ms_iptables
      - mc_proxy: firewall-postconf
      - mc_proxy: ms_iptables-prerestart
    - watch_in:
      - mc_proxy: ms_iptables-postrestart
{%else %}
ms_iptables:
  service.running:
    - enable: true
    - reload: true
    - names:
      - ms_iptables
    - require:
      - service: ms_iptables-conflicting-services
      - mc_proxy: ms_iptables-prerestart
      - file: ms_iptables-/usr/bin/ms_iptables.py
      - file: ms_iptables-/etc/ms_iptables.json
    - require_in:
      - mc_proxy: ms_iptables-postrestart
ms_iptables-reapply:
  cmd.run:
    - name: /usr/bin/ms_iptables.py --from-salt
    - stateful: true
    - watch:
      - service: ms_iptables
      - mc_proxy: ms_iptables-prerestart
    - watch_in:
      - mc_proxy: ms_iptables-postrestart
{%endif %}
{%endif %}
