{% import "makina-states/_macros/salt.sls" as c with context %}

include:
  {% if c.server %}
  - makina-states.services.bootstrap_server
  {% endif %}
  {% if c.sa %}
  - makina-states.services.bootstrap_standalone
  {% endif %}
  {% if c.vm %}
  - makina-states.services.bootstrap_vm
  {% endif %}
  {% if c.no_bootstrap %}
  - makina-states.services.bootstrap
  {% endif %}

# Fix permissions and ownerships
# recurse does not seem to work well to reset perms
etc-salt-dirs-perms:
  cmd.script:
    - source:  {{c.resetperms}}
    - template: jinja
    - msr: {{c.msr}}
    - dmode: 2770
    - fmode: 0770
    - user: "root"
    - group: "{{c.group}}"
    - reset_paths:
      - /etc/salt
    - require:
      - file: etc-salt-dirs
      - service: salt-master
      - service: salt-minion

# recurse does not seem to work well to reset perms
salt-dirs-perms:
  cmd.script:
    - source: {{c.resetperms}}
    - template: jinja
    - dmode: 2770
    - fmode: 0770
    - msr: {{c.msr}}
    - user: "root"
    - group: "{{c.group}}"
    - reset_paths:
      - /srv/salt
      - /srv/.git
      - /srv/pillar
      - /srv/projects
      - /srv/vagrant
    - require:
      - service: salt-master
      - service: salt-minion
      - cmd: salt-git-pull
      - git: SaltTesting-git
      - git: m2crypto
      - file: salt-dirs
      - cmd: etc-salt-dirs-perms
      - group: {{c.group}}
# no more virtualenv at the makina-states level
#    - excludes:
#      - {{c.msr}}/bin
#      - {{c.msr}}/lib
#      - {{c.msr}}/include
#      - {{c.msr}}/local

salt-dirs-restricted-perms:
  cmd.script:
    - source: {{c.resetperms}}
    - template: jinja
    - fmode: 0750
    - msr: {{c.msr}}
    - dmode: 0750
    - user: "root"
    - group: "{{c.group}}"
    - reset_paths:
      - /var/log/salt
      - /var/run/salt
      - /var/cache/salt
      - /etc/salt/pki
    - require:
      - cmd: salt-dirs-perms
      - cmd: etc-salt-dirs-perms
      - file: salt-dirs-restricted
      - service: salt-master
      - service: salt-minion

# recurse does not seem to work well to reset perms
docker-dirs-if-present:
  cmd.script:
    - onlif: ls -d /srv/docker/makinacorpus
    - source: {{c.resetperms}}
    - template: jinja
    - reset_paths:
      - /srv/docker
    - msr: {{c.msr}}
    - dmode: 2770
    - fmode: 0770
    - user: "root"
    - group: {{c.group}}
    - require_in:
      - cmd: update-salt
    - excludes:
      - /srv/docker/docker/bundles
      - /srv/docker/cache
      - /srv/docker/makinacorpus/debian/debootstrap
      - /srv/docker/makinacorpus/ubuntu_deboostrap/debootstrap

