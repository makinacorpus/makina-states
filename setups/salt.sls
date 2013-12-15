{% import "makina-states/_macros/salt.jinja" as c with context %}

include:
  {% if c.mmaster %}
  - makina-states.bootstrap.mastersalt_master
  {% endif %}
  {% if c.mminion %}
  - makina-states.bootstrap.mastersalt_minion
  {% endif %}
  {% if c.devhost %}
  - makina-states.bootstrap.server
  {% endif %}
  {% if c.server %}
  - makina-states.bootstrap.server
  {% endif %}
  {% if c.sa %}
  - makina-states.bootstrap.standalone
  {% endif %}
  {% if c.vm %}
  - makina-states.bootstrap.vm
  {% endif %}
  {% if c.no_bootstrap %}
  - makina-states.bootstrap.base
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
      - {{c.conf_prefix}}
    - require:
      - file: salt-etc-salt-dirs
      - cmd: salt-salt-daemon-proxy-requires-before-restart

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
      - {{c.saltroot}}
      - {{c.prefix}}/.git
      - {{c.pillar_root}}
      - {{c.projects_root}}
      - {{c.vagrant_root}}
    - require:
      - cmd: salt-salt-daemon-proxy-requires-before-restart
      - cmd: etc-salt-dirs-perms

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
      - {{c.log_prefix}}
      - {{c.run_prefix}}
      - {{c.cache_prefix}}
      - {{c.conf_prefix}}/pki
    - require:
      - cmd: salt-dirs-perms
      - cmd: etc-salt-dirs-perms
      - file: salt-salt-dirs-restricted
      - cmd: salt-salt-daemon-proxy-requires-before-restart

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
      - cmd: salt-salt-daemon-proxy-requires-before-restart
    - excludes:
      - {{c.docker_root}}/docker/bundles
      - {{c.docker_root}}/cache
      - {{c.docker_root}}/makinacorpus/debian/debootstrap
      - {{c.docker_root}}/makinacorpus/ubuntu_deboostrap/debootstrap

