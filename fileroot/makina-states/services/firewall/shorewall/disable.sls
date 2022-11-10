include:
  - makina-states.services.firewall.shorewall.hooks
  - makina-states.services.firewall.firewall.hooks
  - makina-states.services.firewall.shorewall.unregister
  - makina-states.services.firewall.firewall.configuration
shorewall-disable-stop-shorewall:
  file.managed:
    - name: /usr/bin/ms_disable_shorewall.sh
    - source: salt://makina-states/files/usr/bin/ms_disable_shorewall.sh
    - mode: 750
    - user: root
    - group: root
    - watch:
      - mc_proxy: shorewall-predisable
    - watch_in:
      - mc_proxy: shorewall-postdisable
  cmd.run:
    - name: /usr/bin/ms_disable_shorewall.sh
    - stateful: true
    - require:
      - file: shorewall-disable-stop-shorewall
    - require_in:
      - mc_proxy: shorewall-postdisable
# only disable if the previous command has run
# but we cant test the rc file as the script removes it
shorewall-disable-firewall:
  cmd.wait:
    - name: /usr/bin/ms_disable_firewall.sh fromsalt nohard
    - stateful: true
    - watch:
      - cmd: shorewall-disable-stop-shorewall
    - require_in:
      - mc_proxy: shorewall-postdisable
shorewall-disable-makinastates-shorewall:
  file.absent:
    - names:
      - /etc/rc.local.d/shorewall.sh
    - watch:
      - cmd: shorewall-disable-stop-shorewall
      - cmd: shorewall-disable-firewall
      - mc_proxy: shorewall-predisable
    - watch_in:
      - mc_proxy: shorewall-postdisable
shorewall-purge-shorewall:
  pkg.purged:
    - pkgs: [shorewall, shorewall6]
    - watch:
      - file: shorewall-disable-makinastates-shorewall
      - mc_proxy: shorewall-predisable
    - watch_in:
      - mc_proxy: shorewall-postdisable
shorewall-uninstall-shorewall:
  pkg.removed:
    - pkgs: [shorewall, shorewall6]
    - watch:
      - pkg: shorewall-purge-shorewall
      - file: shorewall-disable-makinastates-shorewall
      - mc_proxy: shorewall-predisable
    - watch_in:
      - mc_proxy: shorewall-postdisable
