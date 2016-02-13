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

{% macro user_keys(user='root') %}
{{user}}-ssh-keys-init:
  cmd.run:
    - name: |
            home=$(awk -F: -v v="{{user}}" '{if ($1==v && $6!="") print $6}' /etc/passwd)
            if [ ! -e ${home}/.ssh ];then mkdir ${home}/.ssh;fi;
            cd ${home}/.ssh;
            key="id_dsa";
            if [ ! -e ${home}/.ssh/${key} ];then ssh-keygen -f ${key} -t dsa -b 1024 -N ''; fi;
            key="id_rsa";
            if [ ! -e ${home}/.ssh/${key} ];then ssh-keygen -f ${key} -t rsa -b 4096 -N ''; fi;
    - onlyif: |
              home=$(awk -F: -v v="{{user}}" '{if ($1==v && $6!="") print $6}' /etc/passwd)
              ret=1;
              if [ ! -e ${home}/.ssh ];then mkdir ${home}/.ssh;fi;
              cd ${home}/.ssh;
              for i in dsa rsa;do
                key="id_$i";
                if [ ! -e ${home}/.ssh/$key ];then
                  ret=0;
                fi;
              done;
              exit $ret;
    - user: {{user}}
{% endmacro %}
{{ user_keys('root') }}
