disable:
  service.dead:
    - names: [mastersalt-minion,
              mastersalt-master,
              salt-minion,
              salt-master]
    - enable: false
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
    - require:
      - service: disable

up_cron:
  cmd.run:
    - name: |
            for i in /etc/cron.d/salt /etc/cron.d/mastersalt;do
               rm -fv "${i}"
            done
    - require:
      - service: disable
