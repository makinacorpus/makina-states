{% import "makina-states/services/base/ssh/rootkey.sls" as base with context %}
{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.base.ssh.rootkey
{{base.user_keys('vagrant')}}
vagrantvm-install-ssh-keys:
  file.managed:
    - name: /sbin/devhost-installkeys.sh
    - source : ""
    - contents: |
                #!/usr/bin/env bash
                cd /
                users="vagrant root"
                for user in $users;do
                    home=$(awk -F: -v v="$user" '{if ($1==v && $6!="") print $6}' /etc/passwd)
                    if [ -e "$home" ];then
                        rsync\
                            -av\
                            --exclude=authorized_keys* \
                            /mnt/parent_ssh/ "$home/.ssh/"
                        chmod -Rf 700 "$home/.ssh"
                        chown -Rf $user "$home/.ssh"
                    fi
                done
    - user: root
    - mode: 755
    - require_in:
      - cmd: root-ssh-keys-init
  cmd.run:
    - name: /sbin/devhost-installkeys.sh
    - user: root
    - require:
      - file: vagrantvm-install-ssh-keys
    - require_in:
      - cmd: root-ssh-keys-init

cvagrant-root-keygen:
  file.copy:
    - name: /srv/salt/rootkey-dsa.pub
    - makedirs: true
    - source: /root/.ssh/id_dsa.pub
    - watch:
      - cmd: vagrantvm-install-ssh-keys
cvagrant-root-keygen-rsa:
  file.copy:
    - name: /srv/salt/rootkey-rsa.pub
    - makedirs: true
    - source: /root/.ssh/id_rsa.pub
    - watch:
      - cmd: vagrantvm-install-ssh-keys

mcvagrant-root-keygen:
  file.copy:
    - name: /srv/mastersalt/rootkey-dsa.pub
    - makedirs: true
    - source: /root/.ssh/id_dsa.pub
    - watch:
      - cmd: vagrantvm-install-ssh-keys
mcvagrant-root-keygen-rsa:
  file.copy:
    - name: /srv/mastersalt/rootkey-rsa.pub
    - makedirs: true
    - source: /root/.ssh/id_rsa.pub
    - watch:
      - cmd: vagrantvm-install-ssh-keys

{% for user in ['vagrant', 'root'] %}
vagrant-{{user}}-insdsakey:
  ssh_auth.present:
    - source: salt://rootkey-dsa.pub
    - user: root
    - require:
      - file: cvagrant-root-keygen
      - file: mcvagrant-root-keygen
vagrant-{{user}}-inskey:
  ssh_auth.present:
    - source: salt://rootkey-rsa.pub
    - user: root
    - require:
      - file: cvagrant-root-keygen-rsa
      - file: mcvagrant-root-keygen-rsa
{% endfor %}
{% endif %}
