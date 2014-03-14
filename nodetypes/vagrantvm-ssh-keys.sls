vagrantvm-install-ssh-keys:
  cmd.run:
    - name: |
            users="vagrant root"
            for user in $users;do
                home=$(awk -F: -v v="$user" '{if ($1==v && $6!="") print $6}' /etc/passwd)
                if [ -e "$home" ];then
                    rsync\
                        -av\
                        --exclude=authorized_keys* \
                        /mnt/parent_ssh/ "$home/.ssh/"
                    for i in /home/vagrant/.ssh/author*;do
                        dest=$home/.ssh/$(basename $i)
                        if [ "x${i}" != "x${dest}" ];then
                            cp -rvf "$i" "$dest"
                        fi
                    done
                    chmod -Rf 700 "$home/.ssh"
                    chown -Rf $user "$home/.ssh"
                fi
            done
    - user: root
