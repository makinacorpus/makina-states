# see also users.sls
{%- import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'base.ssh') }}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}

include:
  - openssh
  - openssh.config
  - openssh.banner
  - makina-states.localsettings.users
  - makina-states.services.base.ssh-hooks
  - makina-states.services.base.ssh-users

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
      - enable: True
      - watch:
        - file: sshd_config
      {%- if grains['os_family'] == 'Debian' %}
      - name: ssh
      {% else %}
      - name: sshd
      {%- endif %}

  sshd_config:
    file.managed:
      - name: /etc/ssh/sshd_config
      - source: salt://makina-states/files/etc/ssh/sshd_config
      - template: jinja
      - context:
        settings: {{services.sshServerSettings|yaml}}

