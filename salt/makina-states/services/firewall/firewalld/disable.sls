{% if salt['mc_controllers.allow_lowlevel_states']() %}
include:
  - makina-states.services.firewall.firewalld.hooks
  - makina-states.services.firewall.firewall.hooks
  - makina-states.services.firewall.firewalld.unregister
  - makina-states.services.firewall.firewall.configuration
firewalld-disable-makinastates-firewalld:
  file.absent:
    - names:
      - /etc/apt/sources.list.d/firewalld.list
    - watch:
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable
firewalld-stop-firewalld:
  service.dead:
    - names: [firewalld]
    - watch:
      - file: firewalld-disable-makinastates-firewalld
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable
firewalld-purge-firewalld:
  pkg.purged:
    - pkgs: [firewalld]
    - watch:
      - service: firewalld-stop-firewalld
      - file: firewalld-disable-makinastates-firewalld
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable
firewalld-uninstall-firewalld:
  pkg.removed:
    - pkgs: [firewalld]
    - watch:
      - pkg: firewalld-purge-firewalld
      - file: firewalld-disable-makinastates-firewalld
      - mc_proxy: firewalld-predisable
    - watch_in:
      - mc_proxy: firewalld-postdisable
{%endif %}
