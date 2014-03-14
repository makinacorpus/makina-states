vagrantvm-install-ssh-keys:
  cmd.run:
    - name: |
            for user_home in $(awk -F: '{if ($6!="") print $1 ":" $6}' /etc/passwd);do
                user="$(echo $user_home|awk -F: '{print $1}')"
                home="$(echo $user_home|awk -F: '{print $2}')"
                sshf="$home/.ssh"
                if [[ -e "$sshf" ]];then
                    for i in $(ls $sshf);do
                        fulli="$sshf/$i"
                        cleanup=y
                        # only keep authorized* files
                        case $i in
                            author*) cleanup="";
                                ;;
                        esac
                        if [[ -n $cleanup ]];then
                            rm -fvr "$fulli"
                        fi
                    done
                fi
            done
            for i in lxc docker;do
                find /var/lib/${i}/ -name .ssh|while read sshdir;do
                    rm -rfv "${sshdir}/"*
                done
                find /var/lib/${i}/ -name id_dsa* -delete
                find /var/lib/${i}/ -name id_rsa* -delete
            done
    - user: root
