# see also users.sls
include:
  - openssh
  - makina-states.localsettings.users

# Idea is to grant everyone member of "(.-)*makina-users" access
# to managed boxes
# So you need to set a default pillar like that:
# makina-users:
#   keys:
#     mpa:
#       keys:
#         - kiorky.pub
#   users: (opt: default ['root', 'ubuntu' (if ubuntu)])
#     root: {}    # {} is important to mark as dict
#     ubuntu:
#       password: foo
#
# USE     ``python -c "import crypt, getpass, pwd; print crypt.crypt('password', '\$6\$SALTsalt\$')"``
#
# Define any foo-makina-users you want (to make groups, for example)
#
# To override defAult ssh access
# just redifine the needed dictionnay in a specific minion
# matched pillar sls file
# makina-users:
#   keys:
#     foo:
#       bar.pub
#
# The keys are searched in /salt_root/files/ssh/
{% import "makina-states/_macros/vars.jinja" as vars with context %}


{% for user, keys_info in vars.user_keys.items() %}
  {% for k, keys in keys_info.items() %}
    {% for key in keys %}
ssh_auth-{{ user }}-{{ k }}-{{ key }}:
  ssh_auth.present:
    - require:
      - user: {{ user }}
    - comment: key for {{ k }}
    - user: {{ user }}
    - source: salt://files/ssh/{{ key }}
    {% endfor %}
  {% endfor %}
{% endfor %}

extend:
  openssh:
    service.running:
      {% if grains['os'] == 'Debian' %}- name: ssh{% endif %}
      - enable: True
      - watch:
        - file: sshd_config
      {% if grains['os_family'] == 'Debian' %}- name: ssh{% endif %}

  sshd_config:
    file.managed:
      - name: /etc/ssh/sshd_config
      - source: salt://makina-states/files/etc/ssh/sshd_config
      - template: jinja


