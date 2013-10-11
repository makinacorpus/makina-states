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

{% set ms=salt['config.get']('bootstrap:mastersalt', False) -%}
{% set mmaster=salt['config.get']('mastersalt-master', False) -%}
{% set mminion=salt['config.get']('mastersalt-minion', False) -%}
{% set mastersalt=mmaster or mminion or ms -%}
{% set vm=salt['config.get']('bootstrap:makina-states-server', False) -%}
{% set server=salt['config.get']('bootstrap:makina-states-vm', False) -%}
{% set sa=salt['config.get']('bootstrap:makina-states-standalone', False) -%}
{% set msr='/srv/salt/makina-states' %}
{% set group = pillar.get('salt.filesystem.group', 'salt-admin') %}
{% set resetperms = "file://"+msr+"/_scripts/reset-perms.sh" %}

include:
  {% if mastersalt %}
  - makina-states.services.bootstrap_mastersalt
  {% endif %}
  {% if server %}
  - makina-states.services.bootstrap_server
  {% elif sa %}
  - makina-states.services.bootstrap_standalone
  {% endif %}
  {% if vm %}
  - makina-states.services.bootstrap_vm
  {% else %}
  - makina-states.services.bootstrap
  {% endif %}
  {% if mmaster %}
  - makina-states.services.mastersalt_master
  {% endif %}

# Fix permissions and ownerships

# recurse does not seem to work well to reset perms
etc-salt-dirs-perms:
  cmd.script:
    - source:  {{resetperms}}
    - template: jinja
    - msr: {{msr}}
    - fmode: 2770
    - dmode: 0770
    - user: "root"
    - group: "{{group}}"
    - reset_paths:
      - /etc/salt
    - require:
      - file: etc-salt-dirs
      - service: salt-master
      - service: salt-minion

# recurse does not seem to work well to reset perms
salt-dirs-perms:
  cmd.script:
    - source: {{resetperms}}
    - template: jinja
    - fmode: 0770
    - dmode: 2770
    - msr: {{msr}}
    - user: "root"
    - group: "{{group}}"
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
      - group: {{group}}

salt-dirs-restricted-perms:
  cmd.script:
    - source: {{resetperms}}
    - template: jinja
    - fmode: 0750
    - msr: {{msr}}
    - dmode: 0750
    - user: "root"
    - group: "{{group}}"
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
salt-dirs-reset-perms-for-virtualenv:
  cmd.script:
    - source: {{resetperms}}
    - template: jinja
    - reset_paths:
      - {{msr}}/bin
      - {{msr}}/lib
      - {{msr}}/include
      - {{msr}}/local
    - msr: {{msr}}
    - fmode: 0755
    - dmode: 0755
    - user: "root"
    - group: "root"
    - require:
        - cmd: update-salt
        - cmd: salt-dirs-perms
        - cmd: salt-dirs-restricted-perms


# recurse does not seem to work well to reset perms
docker-dirs-if-present:
  cmd.script:
    - onlif: ls -d /srv/docker/ubuntu
    - source: {{resetperms}}
    - template: jinja
    - reset_paths:
      - /srv/docker
    - msr: {{msr}}
    - fmode: 2770
    - dmode: 0770
    - user: "root"
    - group: {{group}}

