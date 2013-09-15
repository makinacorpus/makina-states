{% set salt_modules=[
    '_grains',
    '_macros',
    '_modules',
    '_renderers',
    '_returners',
    '_scripts',
    '_states',] %}

# Keep those 3 following in sync with buildout
salt-git:
  git.latest:
    - name: http://github.com/makinacorpus/salt.git
    - target: /srv/salt/makina-states/src/salt
    - rev: remotes/origin/develop
    - force_checkout: true
SaltTesting-git:
  git.latest:
    - name: http://github.com/saltstack/salt-testing.git
    - target: /srv/salt/makina-states/src/SaltTesting
    - force_checkout: true
m2crypto-git:
  git.latest:
    - name: https://github.com/makinacorpus/M2Crypto.git
    - target: /srv/salt/makina-states/src/m2crypto
    - force_checkout: true

makina-states-dirs:
  file.directory:
    - names:
      {% for i in  salt_modules -%}
      - /srv/salt/{{i}}
      - /srv/salt/makina-states/{{i}}
      {% endfor %}

openssh-formulae:
  git.latest:
    - name: http://github.com/saltstack-formulas/openssh-formula.git
    - target: /srv/salt/formulas/openssh
  file.symlink:
    - target: /srv/salt/formulas/openssh/openssh
    - name: /srv/salt/openssh
    - require:
      - git: openssh-formulae

makina-states:
  git.latest:
    - name: https://github.com/makinacorpus/makina-states.git
    - target: /srv/salt/makina-states

salt-formulae:
  git.latest:
    - name: http://github.com/saltstack-formulas/salt-formula.git
    - target: /srv/salt/formulas/salt
  file.symlink:
    - target: /srv/salt/formulas/salt/salt
    - name: /srv/salt/salt
    - require:
      - git: salt-formulae

salt-modules:
  cmd.run:
    - name: |
            for i in _states _grains _modules _renderers _returners;do
              for f in $(find /srv/salt/makina-states/$i -name "*py" -type f);do
                  ln -vsf "$f" "/srv/salt/$i";
              done;
            done;

openstack-formulae:
  git.latest:
    - name: https://github.com/kiorky/openstack-salt-states.git
    - target: /srv/salt/openstack

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
      - cmd: salt-modules
      - file: makina-states-dirs
      - file: salt-master
      - git: m2crypto-git
      - git: makina-states
      - git: openssh-formulae
      - git: openstack-formulae
      - git: salt-formulae
      - git: salt-git
      - git: SaltTesting-git

salt-minion:
  file.managed:
    - name: /etc/init/salt-minion.conf
    - template: jinja
    - source:  salt://makina-states/files/etc/init/salt-minion.conf
  service.running:
    - enable: True
    - watch:
      - cmd: salt-modules
      - file: makina-states-dirs
      - file: salt-master
      - file: salt-minion-conf
      - git: m2crypto-git
      - git: makina-states
      - git: openssh-formulae
      - git: openstack-formulae
      - git: salt-formulae
      - git: salt-git
      - git: SaltTesting-git
      - service: salt-master

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

{% if grains['os'] == 'Ubuntu' %}
makina-env-bin:
   file.sed:
    - name: /etc/environment
    - before: '({{ saltbinpath }}:)*/usr/local/sbin'
    - after: '{{ saltbinpath }}:/usr/local/sbin'
    - flags: g
{% endif %}

salt-dirs-perms:
  file.directory:
    - names:
      - /var/log/salt
      - /etc/salt
      - /var/run/salt
      - /var/cache/salt
      - /srv/salt
    - user: root
    - group: root
    - dir_mode: 0750
    - recurse: [user, group, mode]

salt-logs:
  file.managed:
    - names:
      - /var/log/salt/key
      - /var/log/salt/master
      - /var/log/salt/minion
      - /var/log/salt/syndic.log
    - mode: 700
  require:
    - service: salt-master
    - service: salt-minion

