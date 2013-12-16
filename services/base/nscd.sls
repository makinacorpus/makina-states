nscd-pkgs:
  pkg.installed:
    - pkgs:
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
      - pkg: nscd-pkgs
      - file: /etc/nsswitch.conf

/etc/nsswitch.conf:
  file.touch: []

