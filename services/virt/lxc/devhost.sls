include:
  - makina-states.services.virt.lxc.hooks
lxcdevhostmount:
  file.managed:
    - name: /sbin/lxc-devhostmount.sh
    - source: salt://makina-states/files/sbin/lxc-devhostmount.sh
    - mode: 750
    - user: root
    - group: root
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf
