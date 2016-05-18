disable:
  service.dead:
    - names: [mastersalt-minion, mastersalt-master,
              salt-minion, salt-master]
    - enable: false
  cmd.run:
    - name: |
        for i in mastersalt-minion mastersalt-master salt-minion salt-master;do
          systemctl mask $i || /bin/true
        done
    - onlyif: systemctl
  file.absent:
    - names:
      - /usr/bin/salt
      - /usr/bin/salt-api
      - /usr/bin/salt-call
      - /usr/bin/salt-cloud
      - /usr/bin/salt-cp
      - /usr/bin/salt-key
      - /usr/bin/salt-master
      - /usr/bin/salt-minion
      - /usr/bin/salt-run
      - /usr/bin/salt-ssh
      - /usr/bin/salt-syndic
      - /usr/bin/salt-unity
      - /etc/cron.d/salt
      - /etc/cron.d/mastersalt
    - require:
      - service: disable
