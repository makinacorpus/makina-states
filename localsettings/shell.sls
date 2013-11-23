#
# basic shell configuration
#
# Make as ubuntu & others do:
# /etc/profile.d contains a collection of shell scripts sourced 
# to construct the base shell environment
#

/etc/profile.d:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 0755
    - file_mode: 0755
    - makedirs: true

makina-etc-profile:
  cmd.run:
    - onlyif: test "$(grep 'profile\.d' /etc/profile|wc -l)" == "0"
    - name: |
            python -c 'print """
            if [ -d /etc/profile.d ]; then
                for i in /etc/profile.d/*.sh; do
                  if [ -r $i ]; then
                    . $i;
                  fi;
                done;
                unset i;
            fi
            """'>> /etc/profile
