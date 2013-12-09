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

makina-etc-profile-acc:
  file.accumulated:
    - filename: /etc/profile
    - text: |

            if [ -d /etc/profile.d ]; then
                for i in /etc/profile.d/*.sh; do
                  if [ -r $i ]; then
                    . $i;
                  fi;
                done;
                unset i;
            fi

    - required_in:
      - file: makina-etc-profile-block

makina-etc-profile-block:
  file.blockreplace:
    - name: /etc/profile
    - marker_start: "# START managed zone profile.d -DO-NOT-EDIT-"
    - marker_end: "# END managed zone profile.d"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True

