{#-
# basic shell configuration
#
# Make as ubuntu & others do:
# /etc/profile.d contains a collection of shell scripts sourced
# to construct the base shell environment
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{- localsettings.register('shell') }}
{%- set locs = localsettings.locations %}
etc-profile-d:
  file.directory:
    - name: {{ locs.conf_dir }}/profile.d
    - user: root
    - group: root
    - dir_mode: 0755
    - file_mode: 0755
    - makedirs: true

makina-etc-profile-acc:
  file.accumulated:
    - filename: {{ locs.conf_dir }}/profile
    - text: |
            if [ -d {{ locs.conf_dir }}/profile.d ]; then
              # only apply if we have no inclusion yet
              if [[ "$(grep -h 'profile\.d' {{ locs.conf_dir }}/profile|wc -l)" -lt "4" ]];then
                for i in {{ locs.conf_dir }}/profile.d/*.sh; do
                  if [ -r $i ]; then
                    . $i;
                  fi;
                done;
                unset i;
              fi
            fi
    - require_in:
      - file: makina-etc-profile-block

makina-etc-profile-block:
  file.blockreplace:
    - name: {{ locs.conf_dir }}/profile
    - marker_start: "# START managed zone profile__d -DO-NOT-EDIT-"
    - marker_end: "# END managed zone profile__d"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
# vim: set nofoldenable:
