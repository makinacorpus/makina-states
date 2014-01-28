# see also users.sls
{%- import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'base.ssh') }}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}

include:
  - makina-states.localsettings.users
  - openssh
  - openssh.config
  - openssh.banner

{#
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
# The keys are searched in /salt_root/files/ssh/
#}
{# By default we generate a dsa+rsa ssh key pair for root #}
root-ssh-keys-init:
  cmd.run:
    - name: |
            if [[ ! -e /root/.ssh ]];then mkdir /root/.ssh;fi;
            cd /root/.ssh;
            for i in dsa rsa;do
              key="id_$i";
              if [[ ! -e /root/.ssh/$key ]];then
                ssh-keygen -f $key -N '';
              fi;
            done;
    - onlyif: |
              ret=1;
              if [[ ! -e /root/.ssh ]];then mkdir /root/.ssh;fi;
              cd /root/.ssh;
              for i in dsa rsa;do
                key="id_$i";
                if [[ ! -e /root/.ssh/$key ]];then
                  ret=0;
                fi;
              done;
              exit $ret;
    - user: root

{%- for user, keys_info in localsettings.user_keys.items() %}
{%-  for commentid, keys in keys_info.items() %}
{%-    for key in keys %}
ssh_auth-{{ user }}-{{ commentid }}-{{ key }}:
  ssh_auth.present:
    - require:
      - user: {{ user }}
    - comment: key for {{ commentid }}
    - user: {{ user }}
    - source: salt://files/ssh/{{ key }}
{%-    endfor %}
{%-  endfor %}
{%- endfor %}
ssh_config:
  file.managed:
    - name: /etc/ssh/ssh_config
    - source: salt://makina-states/files/etc/ssh/ssh_config
    - template: jinja
    - watch_in:
      - service: openssh
    - context:
      settings: {{services.sshClientSettings|yaml}}

extend:
  openssh:
    service.running:
      {%- if grains['os'] == 'Debian' %}
      - name: ssh
      {%- endif %}
      - enable: True
      - watch:
        - file: sshd_config
      {%- if grains['os_family'] == 'Debian' %}
      - name: ssh
      {%- endif %}

  sshd_config:
    file.managed:
      - name: /etc/ssh/sshd_config
      - source: salt://makina-states/files/etc/ssh/sshd_config
      - template: jinja
      - context:
        settings: {{services.sshServerSettings|yaml}}

