nscd-pkgs:
  pkg.installed:
    - names:
      - nscd

nscd-restart:
  cmd.run:
    - name: service nscd restart
    - require:
      - pkg: nscd-pkgs

nscd:
  service.running:
    - enable: True
    - require:
      - cmd: nscd-restart
    - watch:
      - pkg: nscd
      - pkg: nslcd
      - file: /etc/nsswitch.conf

