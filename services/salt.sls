{% set salt_modules=[
    '_grains',
    '_macros',
    '_modules',
    '_renderers',
    '_returners',
    '_scripts',
    '_states',] %}

# Keep those 3 first following in sync with buildout mr.developer content
# those repos are the one needed to bootstrap the core daemons
{% set repos={
  'salt-git': {
    'name': 'http://github.com/makinacorpus/salt.git',
    'rev': 'remotes/origin/develop',
    'target': '/srv/salt/makina-states/src/salt'},
  'SaltTesting-git': {
    'name': 'http://github.com/saltstack/salt-testing.git',
    'target': '/srv/salt/makina-states/src/SaltTesting'},
  'm2crypto': {
    'name': 'https://github.com/makinacorpus/M2Crypto.git',
    'target': '/srv/salt/makina-states/src/m2crypto'},


  'salt-formulae': {
    'name': 'http://github.com/saltstack-formulas/salt-formula.git',
    'target': '/srv/salt/formulas/salt'},
  'openssh-formulae': {
    'name': 'http://github.com/saltstack-formulas/openssh-formula.git',
    'target': '/srv/salt/formulas/openssh'},
  'openstack-formulae': {
    'name': 'https://github.com/kiorky/openstack-salt-states.git',
    'target': '/srv/salt/openstack'},
  'makina-states': {
    'name': 'https://github.com/makinacorpus/makina-states.git',
    'target': '/srv/salt/makina-states'},
} %}
{% for i, data in repos.items() -%}
{% set git=data['target']+'/.git'  -%}
{% set rev=data.get('rev', False) %}
{{i}}:
# on next runs as we reset perms on repos, just set filemode=false
# do not use cwd as if dir does not exist, if will fail the entire state
  cmd.run:
    - name: cd {{data['target']}}  && git config --local core.filemode false
    - onlyif: ls -d {{git}}
# on each run, update the code
  git.latest:
    - name: {{data['name']}}
    - target: {{data['target']}}
    {% if rev %}
    - rev: {{rev}}
    - always_fetch: True
    {% endif %}
    - require:
      - cmd: {{i}}
{% endfor %}

makina-states-dirs:
  file.directory:
    - names:
      {% for i in  salt_modules -%}
      - /srv/salt/{{i}}
      - /srv/salt/makina-states/{{i}}
      {% endfor %}

l-openssh-formulae:
  file.symlink:
    - target: /srv/salt/formulas/openssh/openssh
    - name: /srv/salt/openssh
    - require:
      - git: openssh-formulae

l-salt-formulae:
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
      - file: l-openssh-formulae
      - file: l-salt-formulae
      - git: m2crypto
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
      - git: m2crypto
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
   file.replace:
    - name: /etc/environment
    - pattern: '({{ saltbinpath }}:)*/usr/local/sbin'
    - repl: '{{ saltbinpath }}:/usr/local/sbin'
    - flags: ['MULTILINE', 'DOTALL']
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

# update makina-state
update-salt:
  cmd.run:
    - name: bin/buildout && cat buildout.cfg|md5sum|awk '{print $1}'>.saltcheck
    - unless: test "$(cat buildout.cfg|md5sum|awk '{print $1}')" = "$(cat .saltcheck)"
    - cwd: /srv/salt/makina-states
    - require:
      - git: salt-git
    - watch_in:
      - service: salt-master
      - service: salt-minion 

