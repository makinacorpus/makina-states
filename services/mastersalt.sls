mastersalt-minion-conf:
  file.managed:
    - name: /etc/mastersalt/minion
    - template: jinja
    - source: salt://makina-states/files/etc/mastersalt/minion

mastersalt-minion:
  file.managed:
    - name: /etc/init/mastersalt-minion.conf
    - template: jinja
    - source:  salt://makina-states/files/etc/init/mastersalt-minion.conf
  service.running:
    - enable: True
    - require:
      - file: salt-profile
      - file: salt-env
    - watch:
      - file: mastersalt-minion-conf

mastersalt-minion-cache:
  file.directory:
    - name: /var/cache/salt/mastersalt/minion
    - mode: 700
    - makedirs: True

mastersalt-minion-sock:
  file.directory:
    - name: /var/run/salt/mastersalt-minion
    - mode: 700
    - makedirs: True
