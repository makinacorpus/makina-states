include:
  - makina-states.services.salt

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

mastersalt-salt-bin:
  file.managed:
    - name: /usr/bin/mastersalt
    - source: salt://makina-states/files/usr/bin/mastersalt
    - mode: 755
    - makedirs: True

mastersalt-saltcall-bin:
  file.managed:
    - name: /usr/bin/mastersalt-call
    - source: salt://makina-states/files/usr/bin/mastersalt-call
    - mode: 755
    - makedirs: True

mastersalt-minion-logs:
  file.managed:
    - names:
      - /var/log/salt/mastersalt-minion
    - mode: 700
  require:
    - service: mastersalt-minion


mastersalt-dirs-perms:
  file.directory:
    - names:
      - /etc/mastersalt
    - user: root
    - group: root
    - mode: 700
    - recurse: [user, group, mode]

