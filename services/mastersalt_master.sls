# As described in wiki each server has a local master
# but can also be controlled via the mastersalt via the syndic interface.
# We have the local master in /etc/salt
# We have the running syndic/master/minion in /etc/salt
# and on mastersalt, we have another master daemon configured in /etc/mastersalt

{% import "makina-states/_macros/salt.sls" as c with context %}

include:
  - makina-states.services.mastersalt

mastersalt-key-bin:
  file.managed:
    - name: {{c.msr}}/bin/mastersalt-key
    - source: salt://makina-states/files/usr/bin/mastersalt-key
    - mode: 755
    - makedirs: True

mastersalt-master-conf:
  file.managed:
    - name: /etc/mastersalt/master
    - template: jinja
    - source: salt://makina-states/files/etc/mastersalt/master

mastersalt-master-job:
  file.managed:
    - name: /etc/init/mastersalt-master.conf
    - source: salt://makina-states/files/etc/init/mastersalt.conf

mastersalt-master-cache:
  file.directory:
    - name: /var/cache/mastersalt/master
    - makedirs: True

mastersalt-master-pki:
  file.directory:
    - name: /etc/mastersalt/pki/master
    - makedirs: True
    - require:
      - file: etc-mastersalt-dirs

mastersalt-master-sock-dir:
  file.directory:
    - name: /var/run/salt/mastersalt-master
    - makedirs: True

mastersalt-master-logs:
  file.managed:
    - names:
      - /var/log/salt/mastersalt-key
      - /var/log/salt/mastersalt-master
      - /var/log/salt/mastersalt-syndic.log

# done to mitigate authentication errors on restart
restart-mastersalt-master:
  cmd.run:
    - name: |
            service mastersalt-master restart &&\
            echo "Reloading mastersalt-master" &&\
            rm -f "{c.msr}}/.restart_msalt"
    - onlyif: ls "{{c.msr}}/.restart_msalt"
    - require:
      - cmd: mastersalt-daemon-proxy-requires-before-restart
      - file: mastersalt-master-cache
      - file: mastersalt-master-conf
      - file: mastersalt-master-job
      - file: mastersalt-master-pki
      - file: mastersalt-master-logs
      - file: mastersalt-saltcall-bin
      - file: mastersalt-master-sock-dir
    - require_in:
      - cmd: restart-mastersalt-minion

mastersalt-master:
  service.running:
    - enable: True
    - require:
      - cmd: restart-mastersalt-master

mastersalt-master-grain:
  grains.present:
    - name: makina.mastersalt-master
    - value: True
    - require_in:
      - cmd: salt-reload-grains
    - require:
      - service: mastersalt-master


