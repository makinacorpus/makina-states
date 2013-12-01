{% import "makina-states/_macros/salt.jinja" as c with context %}

include:
  - makina-states.services.base.salt

salt-master-conf:
  file.managed:
    - name: /etc/salt/master
    - template: jinja
    - source: salt://makina-states/files/etc/salt/master
    - require:
      - file: etc-salt-dirs

salt-master-job:
  file.managed:
    - name: /etc/init/salt-master.conf
    - template: jinja
    - source: salt://makina-states/files/etc/init/salt-master.conf

salt-master:
  service.running:
    - enable: True
    - require:
      - cmd: restart-salt-master

salt-master-cache:
  file.directory:
    - name: /var/cache/salt/master
    - makedirs: True

salt-master-pki:
  file.directory:
    - name: /etc/salt/pki/master
    - makedirs: True
    - require:
      - file: etc-salt-dirs

salt-master-sock-dir:
  file.directory:
    - name: /var/run/salt/salt
    - makedirs: True

salt-master-logs:
  file.managed:
    - names:
      - /var/log/salt/key
      - /var/log/salt/master
      - /var/log/salt/syndic.log

# done to mitigate authentication errors on restart
restart-salt-master:
  cmd.run:
    - name: |
            service salt-master restart &&\
            echo "Reloading salt-master" &&\
            rm -f "{{c.msr}}/.restart_salt"
    - onlyif: ls "{{c.msr}}/.restart_salt"
    - require:
      - cmd: salt-daemon-proxy-requires-before-restart
      - file: salt-master-cache
      - file: salt-master-conf
      - file: salt-master-job
      - file: salt-master-pki
      - file: salt-master-logs
      - file: salt-master-sock-dir
    - require_in:
      - cmd: restart-salt-minion

salt-master-grain:
  grains.present:
    - name: makina.salt-master
    - value: True
    - require_in:
      - cmd: salt-reload-grains
    - require:
      - service: salt-master

