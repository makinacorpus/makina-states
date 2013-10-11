#
# Salt base installation
# We set
#   - salt root in /srv/salt
#   - salt conf in /etc/salt
#   - pillar in /srv/pillar
#   - projects code source is to be managed in /srv/projects
#
# We create a group called salt-admin which has rights in /srv/{pillar, salt, projects}
#

{% set group = pillar.get('salt.filesystem.group', 'salt-admin') %}
{% set group_id = pillar.get('salt.filesystem.gid', 65753) %}
{% set msr='/srv/salt/makina-states' %}
{% set saltbinpath = msr+'/bin' %}

{% set salt_modules=[
    '_grains',
    '_macros',
    '_modules',
    '_renderers',
    '_returners',
    '_scripts',
    '_states',] %}

# only here for orchestration purposes
dummy-pre-salt-checkouts:
  cmd.run:
    - name: /bin/true
    - unless: /bin/true

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
    - name: cd "{{data['target']}}" && git config --local core.filemode false
    - require:
      - cmd: dummy-pre-salt-checkouts
    - onlyif: ls -d "{{git}}"
    - unless: if [[ -d "{{git}}" ]];then cd "{{data['target']}}" && grep -q "filemode = false" .git/config;fi
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
    - unless: |
              for i in _states _grains _modules _renderers _returners;do
                for f in $(find /srv/salt/makina-states/$i -name "*py" -type f);do
                  dest="$f";
                  sym="/srv/salt/$i/$(basename $f)";
                  if [[ ! -e  "$sym" ]];then
                    echo "$sym not present";
                    exit -1;
                  fi;
                  if [[ -h "$sym" ]];then
                    if [[ "$(readlink $sym)" != "$dest" ]];then
                      echo "$sym != $dest";
                      exit -1;
                    fi;
                  fi;
                done;
              done;
              exit 0;

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
      - service: salt-minion
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

# # make a proxy between service and master for when
# # there is a master restart to let minions re-auth
# salt-minion-wait-restart:
#   cmd.run:
#     - name: sleep 13
#     - watch_in:
#      - file:salt-minion-job
#     - watch:
#       - cmd: salt-modules
#       - file: makina-states-dirs
#       - file: salt-master
#       - file: salt-minion-conf
#       - git: m2crypto
#       - git: makina-states
#       - git: openssh-formulae
#       - git: openstack-formulae
#       - git: salt-formulae
#       - git: SaltTesting-git
#       - service: salt-master

salt-minion-job:
  file.managed:
    - name: /etc/init/salt-minion.conf
    - template: jinja
    - source:  salt://makina-states/files/etc/init/salt-minion.conf

salt-minion:
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
      - file: salt-minion-job

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
    - makedirs: True

salt-master-cache:
  file.directory:
    - name: /var/cache/salt/master
    - makedirs: True

minion-sock:
  file.directory:
    - name: /var/run/salt/minion
    - makedirs: True

salt-sock:
  file.directory:
    - name: /var/run/salt/salt
    - makedirs: True

salt-pki:
  file.directory:
    - name: /etc/salt/pki/master
    - makedirs: True

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

{{group}}:
  group.present:
    - system: True
    {% if group_id %}- gid: {{group_id}}{% endif %}

# this is really factored
# idea is to create dirs, then requires daemons to issue the chmod
# without restarting them, otherwise the watch function will
# restart them everytime !
etc-salt-dirs:
  file.directory:
    - names:
      - /etc/salt
      - /etc/salt/master.d
      - /etc/salt/minion.d
    - user: root
    - group: {{group}}
    - dir_mode: 2770
    - makedirs: True
    - require:
      - group: {{group}}

salt-dirs:
  file.directory:
    - names:
      - /srv/salt
      - /srv/pillar
      - /srv/projects
      - /srv/vagrant
    - user: root
    - group: {{group}}
    - file_mode: "0770"
    - dir_mode: "2770"
    - makedirs: True

salt-dirs-restricted:
  file.directory:
    - names:
      - /var/log/salt
      - /var/run/salt
      - /var/cache/salt
      - /etc/salt/pki
    - msr: {{msr}}
    - user: root
    - group: {{group}}
    - file_mode: 0750
    - dir_mode: 0750
    - makedirs: True
    - require:
      - file: salt-dirs

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

# non blocking gitpull
salt-git-pull:
  cmd.run:
    - name: git pull;exit 0
    - cwd: {{msr}}/src/salt
    - onlyif: ls -d {{msr}}/src/salt/.git
    - require_in:
      - service: salt-master
      - service: salt-minion

# update makina-state
salt-buildout-bootstrap:
  cmd.run:
    - name: python bootstrap.py
    - cwd: {{msr}}
    - unless: test "$(cat buildout.cfg|md5sum|awk '{print $1}')" = "$(cat .saltcheck)"
    - require_in:
      - cmd: update-salt
    - require:
      - git: makina-states

update-salt:
  cmd.run:
    - name: bin/buildout && cat buildout.cfg|md5sum|awk '{print $1}'>.saltcheck
    - unless: test "$(cat buildout.cfg|md5sum|awk '{print $1}')" = "$(cat .saltcheck)"
    - cwd: /srv/salt/makina-states
    - require_in:
      - service: salt-master
      - service: salt-minion
    - watch_in:
      - service: salt-master
      - service: salt-minion
