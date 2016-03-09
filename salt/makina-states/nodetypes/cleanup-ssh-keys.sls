vagrantvm-cleanup-ssh-keys:
  file.managed:
    - name: /sbin/ms-cleanup-sshkeys.sh
    - contents: |
                #!/usr/bin/env bash
                for user_home in $(awk -F: '{if ($6!="") print $1 ":" $6}' /etc/passwd);do
                    user="$(echo $user_home|awk -F: '{print $1}')"
                    home="$(echo $user_home|awk -F: '{print $2}')"
                    sshf="$home/.ssh"
                    if [ -e "$sshf" ];then
                        for i in $(ls $sshf);do
                            fulli="$sshf/$i"
                            cleanup=y
                            # only keep authorized* files
                            case $i in
                                author*) cleanup="";
                                    ;;
                            esac
                            if [ "x${cleanup}" != "x" ];then
                                rm -fvr "$fulli"
                            fi
                        done
                    fi
                done
                for i in lxc docker;do
                    find /var/lib/${i}/ -name .ssh|while read sshdir;do
                        rm -rfv "${sshdir}/"*
                    done
                    find /var/lib/${i}/ -name id_dsa* |xargs rm -fv
                    find /var/lib/${i}/ -name id_rsa* |xargs rm -fv
                done
                for i in /srv/lxc/*;do
                    find ${i} -name .ssh|while read sshdir;do
                        rm -rfv "${sshdir}/"*
                    done
                    find ${i}/ -name id_dsa* | xargs rm -fv
                    find ${i}/ -name id_rsa* | xargs rm -fv
                done
    - user: root
    - mode: 755
    - require_in:
      - cmd: vagrantvm-cleanup-ssh-keys
  cmd.run:
    - name: /sbin/ms-cleanup-sshkeys.sh
    - user: root
