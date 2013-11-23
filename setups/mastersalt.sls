{% import "makina-states/_macros/salt.sls" as c with context %}
{% if c.mastersalt %}
include:
  {% if c.mmaster %}
  - makina-states.services.bootstrap_mastersalt_master
  {% else %}
  - makina-states.services.bootstrap_mastersalt
  {% endif %}

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
      - cmd: mastersalt-daemon-proxy-requires-before-restart
      - file: etc-mastersalt-dirs

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
      - cmd: mastersalt-daemon-proxy-requires-before-restart
{% endif %}
