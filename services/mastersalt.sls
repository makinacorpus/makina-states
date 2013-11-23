# As described in wiki each server has a local master
# but can also be controlled via the mastersalt via the syndic interface.
# We have the local master in /etc/salt
# We have the running syndic/master/minion in /etc/salt
# and on mastersalt, we have another master daemon configured in /etc/mastersalt

{% import "makina-states/_macros/salt.sls" as c with context %}

include:
  - makina-states.services.salt

mastersalt-salt-bin:
  file.managed:
    - name: {{c.msr}}/bin/mastersalt
    - source: salt://makina-states/files/usr/bin/mastersalt
    - mode: 755
    - makedirs: True
    - require:
      - cmd: update-salt

mastersalt-saltcall-bin:
  file.managed:
    - name: {{c.msr}}/bin/mastersalt-call
    - source: salt://makina-states/files/usr/bin/mastersalt-call
    - mode: 755
    - makedirs: True
    - require:
      - cmd: update-salt
    - require-in:
      - cmd: update-salt
      - service: mastersalt-minion

mastersalt-minion-conf:
  file.managed:
    - name: /etc/mastersalt/minion
    - template: jinja
    - source: salt://makina-states/files/etc/mastersalt/minion

mastersalt-minion-job:
  file.managed:
    - name: /etc/init/mastersalt-minion.conf
    - template: jinja
    - source:  salt://makina-states/files/etc/init/mastersalt-minion.conf

mastersalt-minion-cache:
  file.directory:
    - name: /var/cache/mastersalt/minion
    - makedirs: True

mastersalt-minion-sock-dir:
  file.directory:
    - name: /var/run/salt/mastersalt-minion
    - makedirs: True

mastersalt-minion-pki:
  file.directory:
    - name: /etc/mastersalt/pki/minion
    - makedirs: True
    - require:
      - file: etc-mastersalt-dirs

mastersalt-minion-logs:
  file.managed:
    - names:
      - /var/log/salt/mastersalt-minion

# this is really factored
# idea is to create dirs, then requires daemons to issue the chmod
# without restarting them, otherwise the watch function will
# restart them everytime !
etc-mastersalt-dirs:
  file.directory:
    - names:
      - /etc/mastersalt
      - /etc/mastersalt/master.d
      - /etc/mastersalt/minion.d
    - user: root
    - group: {{c.group}}
    - dir_mode: 2770
    - makedirs: True
    - require:
      - group: {{c.group}}

mastersalt-dirs-restricted:
  file.directory:
    - names:
      - /var/log/mastersalt
      - /var/cache/mastersalt
      - /etc/mastersalt/pki
    - msr: {{c.msr}}
    - user: root
    - group: {{c.group}}
    - file_mode: 0750
    - dir_mode: 2750
    - makedirs: True
    - require:
      - file: etc-mastersalt-dirs

mastersalt-logrotate:
  file.managed:
    - template: jinja
    - name: /etc/logrotate.d/mastersalt.conf
    - source: salt://makina-states/files/etc/logrotate.d/mastersalt.conf
    - rotate: {{ c.rotate }}

# before being really restarted
mastersalt-daemon-proxy-requires-before-restart:
  cmd.run:
    - name: echo "dummy"
    - require_in:
      - cmd: update-salt
      - cmd: salt-daemon-proxy-requires-before-restart
      - file: etc-mastersalt-dirs
      - file: mastersalt-dirs-restricted
      - file: mastersalt-logrotate
      - file: mastersalt-minion-cache
      - file: mastersalt-minion-conf
      - file: mastersalt-minion-job
      - file: mastersalt-minion-logs
      - file: mastersalt-minion-pki
      - file: mastersalt-minion-sock-dir

# done to mitigate authentication errors on restart
restart-mastersalt-minion:
  cmd.run:
    - name: |
            service mastersalt-minion stop;\
            service mastersalt-minion restart &&\
            echo "Reloading mastersalt-minion" &&\
            sleep 5 &&\
            rm -f "{{c.msr}}/.restart_msalt_minion"
    - onlyif: ls "{{c.msr}}/.restart_msalt_minion"
    - require:
      - cmd: mastersalt-daemon-proxy-requires-before-restart

mastersalt-minion:
  service.running:
    - enable: True
    - require:
      - cmd: restart-mastersalt-minion

mastersalt-minion-grain:
  grains.present:
    - name: makina.mastersalt-minion
    - value: True
    - require_in:
      - cmd: salt-reload-grains
    - require:
      - service: mastersalt-minion


