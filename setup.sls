# The setup of makina-states is responsible for
# installing and keeping up & running the base salt infrastructure
#
# It will look in pillar & grains which bootstrap to apply.
# Indeed, at bootstrap stage, we had set a grain to tell which one we had
# run and we now have enougth context to know how and what to upgrade.
# So, this setup state will at least extend the used boostrap state.
#
# - Steps of updating makina-states
#   - Update code
#   - Maybe Re buildout bootstrap & buildout which update some other
#     parts of the code and install new core python libraries & scripts
#   - Install base system prerequisites & configuration
#   - Install salt/mastersalt infrastructure & base pkgs
#   - Take care of file mode and ownership deployed by salt (see below)
#
{% import "makina-states/_macros/salt.sls" as c with context %}

include:
  {% if c.mastersalt %}
  {% if c.mmaster %}
  - makina-states.services.bootstrap_mastersalt_master
  {% else %}
  - makina-states.services.bootstrap_mastersalt
  {% endif %}
  {% endif %}
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
    - onlif: ls -d /srv/docker/ubuntu
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
      - /docker/docker/bundles
      - /docker/debian/cache
      - /docker/debian/debootstrap
      - /docker/ubuntu-debootstrap/cache
      - /docker/ubuntu-debootstrap/debootstrap

{% if c.mastersalt %}
# recurse does not seem to work well to reset perms
etc-mastersalt-dirs-perms:
  cmd.script:
    - source:  {{c.resetperms}}
    - template: jinja
    - msr: {{c.msr}}
    - dmode: 2770
    - fmode: 0770
    - user: "root"
    - group: "{{c.group}}"
    - reset_paths:
      - /etc/mastersalt
    - require:
      - file: etc-mastersalt-dirs
      - service: mastersalt-minion
      {% if c.mmaster %}- service: mastersalt-master{% endif %}

mastersalt-dirs-restricted-perms:
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
      - /var/cache/mastersalt
      - /etc/mastersalt/pki
    - require:
      - cmd: etc-mastersalt-dirs-perms
      - service: mastersalt-minion
      {% if c.mmaster %}- service: mastersalt-master{% endif %}
{% endif %}
