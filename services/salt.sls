salt-master-conf:
  file.managed:
    - name: /etc/salt/master
    - template: jinja
    - source: salt://makina-states/files/etc/salt/master

salt-minion-conf:
  file.managed:
    - name: /etc/salt/minion
    - template: jinja
    - source: salt://makina-states/files/etc/salt/minion

salt-master:
  file.managed:
    - name: /etc/init/salt-master.conf
    - template: jinja
    - source: salt://makina-states/files/etc/init/salt-master.conf
  service.running:
    - enable: True
    - watch:
      - file: salt-master

salt-minion:
  file.managed:
    - name: /etc/init/salt-minion.conf
    - template: jinja
    - source:  salt://makina-states/files/etc/init/salt-minion.conf
  service.running:
    - enable: True
    - watch:
      - file: salt-minion-conf



# disabled, syndic cannot sync files !
# salt-syndic:
#   file.managed:
#     - name: /etc/init/salt-syndic.conf
#     - template: jinja
#     - source:  salt://makina-states/files/etc/init/salt-syndic.conf
#   service.running:
#     - enable: True
#     - watch:
#       - file: salt-master-conf

salt-minion-cache:
  file.directory:
    - name: /var/cache/salt/minion
    - mode: 700
    - makedirs: True

salt-master-cache:
  file.directory:
    - name: /var/cache/salt/master
    - mode: 700
    - makedirs: True

minion-sock:
  file.directory:
    - name: /var/run/salt/minion
    - mode: 700
    - makedirs: True


salt-sock:
  file.directory:
    - name: /var/run/salt/salt
    - mode: 700
    - makedirs: True

salt-pki:
  file.directory:
    - name: /etc/salt/pki/master
    - mode: 700
    - makedirs: True

salt-profile:
  file.managed:
    - name: /etc/profile.d/salt.sh
    - source: salt://makina-states/files/etc/profile.d/salt.sh
    - mode: 755
    - require_in:
      - service: salt-master
      - service: salt-minion
#      - service: salt-syndic

{% set saltbinpath = '/srv/salt/makina-states/bin' %}
salt-env:
  file.managed:
    - name: /etc/profile.d/salt.sh
    - source: salt://makina-states/files/etc/profile.d/salt.sh
    - mode: 755
    - template: jinja
    - saltbinpath: {{ saltbinpath }}
    - require_in:
      - service: salt-master
      - service: salt-minion
      - service: mastersalt-minion
#      - service: salt-syndic

{% if grains['os'] == 'Ubuntu' %}
makina-env-bin:
   file.sed:
    - name: /etc/environment
    - before: '({{ saltbinpath }}:)*/usr/local/sbin'
    - after: '{{ saltbinpath }}:/usr/local/sbin'
    - flags: g
{% endif %}


