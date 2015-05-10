{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.firewall.shorewall.hooks
shorewall-disable-stop-shorewall:
  file.managed:
    - name: /usr/bin/disable-shorewall.sh
    - source: salt://makina-states/files/usr/bin/disable-shorewall.sh
    - mode: 750
    - user: root
    - group: root
  cmd.run:
    - name: /usr/bin/disable-shorewall.sh
    - watch:
      - file: shorewall-disable-stop-shorewall
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: shorewall-prerestart

shorewall-disable-makinastates-shorewall:
  file.absent:
    - names:
      - /etc/rc.local.d/shorewall.sh
    - watch:
      - cmd: shorewall-disable-stop-shorewall
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: shorewall-prerestart

shorewall-uninstall-shorewall:
  pkg.removed:
    - pkgs: [shorewall, shorewall6]
    - watch:
      - file: shorewall-disable-makinastates-shorewall
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: shorewall-prerestart
{%endif %}
