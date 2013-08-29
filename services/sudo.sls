sudo:
  pkg.installed

sudoers:
   file.managed:
    - name: /etc/sudoers
    - source: salt://makina-states/files/etc/sudoers
    - mode: 440
    - template: jinja

