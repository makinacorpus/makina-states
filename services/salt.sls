#
# Salt base installation
# We set
#   - salt root in /srv/salt
#   - salt conf in /etc/salt
#   - pillar in /srv/pillar
#   - projects code source is to be managed in /srv/projects
#
# This state file only install a minion
#
# We create a group called editor which has rights in /srv/{pillar, salt, projects}
#

{% import "makina-states/_macros/salt.sls" as c with context %}
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
      {% for i in salt_modules -%}
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
              if [[ ! -d  "/srv/salt/$i" ]];then mkdir "/srv/salt/$i";fi;
              for f in $(find {{c.msr}}/$i -name "*py" -type f);do
                  ln -vsf "$f" "/srv/salt/$i";
              done;
            done;
    - unless: |
              for i in _states _grains _modules _renderers _returners;do
                for f in $(find {{c.msr}}/$i -name "*py" -type f);do
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

salt-reload-grains:
  cmd.script:
    - source: salt://makina-states/_scripts/reload_grains.sh
    - template: jinja

#salt-test-grain:
#  grains.present:
#    - name: makina.test
#    - value: True
#    - require_in:
#      - cmd: salt-reload-grains
#  cmd.run:
#    - name: salt-call --local grains.get makina.test
#    - require:
#      - grains: salt-test-grain

salt-minion-conf:
  file.managed:
    - name: /etc/salt/minion
    - template: jinja
    - source: salt://makina-states/files/etc/salt/minion

salt-minion-job:
  file.managed:
    - name: /etc/init/salt-minion.conf
    - template: jinja
    - source:  salt://makina-states/files/etc/init/salt-minion.conf

salt-minion:
  service.running:
    - enable: True
    - require:
        - cmd: restart-salt-minion

salt-minion-grain:
  grains.present:
    - name: makina.salt-minion
    - value: True
    - require_in:
      - cmd: salt-reload-grains
    - require:
      - service: salt-minion

salt-minion-cache:
  file.directory:
    - name: /var/cache/salt/minion
    - makedirs: True

salt-minion-sock-dir:
  file.directory:
    - name: /var/run/salt/minion
    - makedirs: True

salt-minion-pki:
  file.directory:
    - name: /etc/salt/pki/minion
    - makedirs: True
    - require:
      - file: etc-salt-dirs

salt-env:
  file.managed:
    - name: /etc/profile.d/salt.sh
    - source: salt://makina-states/files/etc/profile.d/salt.sh
    - mode: 755
    - template: jinja
    - saltbinpath: {{ c.saltbinpath }}

{% if grains['os'] == 'Ubuntu' %}
makina-env-bin:
   file.replace:
    - name: /etc/environment
    - pattern: '({{ c.saltbinpath }}:)*/usr/local/sbin'
    - repl: '{{ c.saltbinpath }}:/usr/local/sbin'
    - flags: ['MULTILINE', 'DOTALL']
{% endif %}

{{c.group}}:
  group.present:
    - system: True
    {% if c.group_id %}- gid: {{c.group_id}}{% endif %}

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
    - group: {{c.group}}
    - dir_mode: 2770
    - makedirs: True
    - require:
      - group: {{c.group}}

salt-dirs:
  file.directory:
    - names:
      - /srv/salt
      - /srv/pillar
      - /srv/projects
      - /srv/vagrant
    - user: root
    - group: {{c.group}}
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
    - msr: {{c.msr}}
    - user: root
    - group: {{c.group}}
    - file_mode: 0750
    - dir_mode: 2750
    - makedirs: True
    - require:
      - file: salt-dirs

salt-minion-logs:
  file.managed:
    - names:
      - /var/log/salt/minion

# non blocking gitpull
salt-git-pull:
  cmd.run:
    - name: |
            branch=$(git symbolic-ref -q --short HEAD);
            if [[ -z "$branch" ]];then
                git checkout develop;
            fi;
            git pull origin develop;
            exit 0
    - cwd: {{c.msr}}/src/salt
    - onlyif: ls -d {{c.msr}}/src/salt/.git

# update makina-state
salt-logrotate:
  file.managed:
    - template: jinja
    - name: /etc/logrotate.d/salt.conf
    - source: salt://makina-states/files/etc/logrotate.d/salt.conf
    - rotate: {{ c.rotate }}

# update makina-state
salt-buildout-bootstrap:
  cmd.run:
    - name: |
            py="python";
            if [ -e "/salt-venv/bin/python" ];then 
              py="/salt-venv/bin/python";
            fi;
            $py bootstrap.py
    - cwd: {{c.msr}}
    - unless: test "$(cat buildout.cfg|md5sum|awk '{print $1}')" = "$(cat .saltcheck)"
    - require_in:
      - cmd: update-salt
    - require:
      - git: makina-states

update-salt:
  cmd.run:
    - name: |
            bin/buildout &&\
            cat buildout.cfg|md5sum|awk '{print $1}'>.saltcheck &&\
            touch "{{c.msr}}/.restart_salt" &&\
            touch "{{c.msr}}/.restart_msalt" &&\
            touch "{{c.msr}}/.restart_salt_minion" &&\
            touch "{{c.msr}}/.restart_msalt_minion"
    - cwd: {{c.msr}}
    - unless: test "$(cat buildout.cfg|md5sum|awk '{print $1}')" = "$(cat .saltcheck)"

# done to mitigate authentication errors on restart
restart-salt-minion:
  cmd.run:
    - name: |
            service salt-minion stop ;\
            service salt-minion start &&\
            echo "Reloading salt-minion" &&\
            sleep 5 &&\
            rm -f "{{c.msr}}/.restart_salt_minion"
    - onlyif: ls "{{c.msr}}/.restart_salt_minion"
    - require:
      - cmd: salt-daemon-proxy-requires-before-restart
      - file: salt-minion-cache
      - file: salt-minion-conf
      - file: salt-minion-job
      - file: salt-minion-logs
      - file: salt-minion-pki
      - file: salt-minion-sock-dir

# salt master state will attach to this for the minion to be configured
# before being really restarted
salt-daemon-proxy-requires-before-restart:
  cmd.run:
    - name: echo "dummy"
    - require_in:
      - cmd: update-salt
    - require:
      - cmd: salt-git-pull
      - cmd: salt-modules
      - file: l-openssh-formulae
      - file: l-salt-formulae
      - file: salt-env
      - git: m2crypto
      - git: makina-states
      - git: openssh-formulae
      - git: openstack-formulae
      - git: salt-formulae
      - file: etc-salt-dirs
      - file: salt-dirs-restricted
      - file: salt-logrotate

