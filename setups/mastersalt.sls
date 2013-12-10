{% import "makina-states/_macros/salt.jinja" as c with context %}
{% if c.mastersalt %}
include:
  {% if c.mmaster %}
  - makina-states.bootstrap.mastersalt_master
  {% else %}
  - makina-states.bootstrap.mastersalt_minion
  {% endif %}

# recurse does not seem to work well to reset perms
mastersalt-dirs-perms:
  cmd.script:
    - source:  {{c.resetperms}}
    - template: jinja
    - msr: {{c.mmsr}}
    - dmode: 2770
    - fmode: 0770
    - user: "root"
    - group: "{{c.group}}"
    - reset_paths:
      - /etc/mastersalt
      - /srv/mastersalt-pillar
      - /srv/mastersalt
    - require:
      - cmd: salt-mastersalt-daemon-proxy-requires-before-restart
      - file: salt-etc-mastersalt-dirs

mastersalt-dirs-restricted-perms:
  cmd.script:
    - source: {{c.resetperms}}
    - template: jinja
    - fmode: 0750
    - msr: {{c.mmsr}}
    - dmode: 0750
    - user: "root"
    - group: "{{c.group}}"
    - reset_paths:
      - /var/log/salt
      - /var/run/mastersalt
      - /var/run/salt
      - /var/cache/mastersalt
      - /etc/mastersalt/pki
    - require:
      - cmd: mastersalt-dirs-perms
      - cmd: salt-mastersalt-daemon-proxy-requires-before-restart
{% endif %}
