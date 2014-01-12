# See also makina-states.services.base.ssh.sls
#
# to generate a password hash
# USE ``python -c "import crypt, getpass, pwd; print crypt.crypt('password', '\$6\$SALTsalt\$')"``
# or python
# >>> import crypt, getpass, pwd; print crypt.crypt('password', '$6$SALTsalt$')
#
#
# Idea is to create any user/group needed for ssh managment

{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}

{{ localsettings.register('users') }}
{% set locs = localsettings.locations %}

{% for id, udata in localsettings.users.items() %}
{% set password = udata.get('password', False) %}
{% set home = udata['home'] %}
{% set bashrc = home + '/.bashrc' %}
{% set bashprofile = home + '/.bash_profile' %}
{{ id }}:
  group.present:
    - name: {{ id }}
    - system: True
  user.present:
    - name: {{ id }}
    - require:
        - group: {{ id }}
    {%- if id not in ['root'] %}
    - fullname: {{ id }} user
    - createhome: True
    - shell: /bin/bash
    - home: {{ home }}
    - gid_from_name: True
    - remove_groups: False
    {% if password %}- password:  {{ password }} {% endif %}
    - optional_groups:
      - {{ id }}
      - cdrom
      - audio
      - dip
      - plugdev
      - games
      - sambashare
      {%- if udata.get('admin', False) %}
      - lpadmin
      - sudo
      - adm
      {%- if grains['os_family'] != 'Debian' %}
      - admin
      - wheel
      {% endif %}
      {% endif %}
      {% endif %}

makina-{{id}}-bashfiles:
  file.touch:
    - names:
        - {{bashrc}}
        - {{bashprofile}}
    - user: {{id}}
    - group: {{id}}
    - require_in:
      - file: makina-{{id}}-bashprofile-load

makina-{{id}}-bashprofile-load-acc:
  file.accumulated:
    - filename: {{bashprofile}}
    - text: |
            if [[ -f '{{ locs.conf_dir }}/profile' ]];then
              # only apply if we have no inclusion yet
              if [[ "$(grep -h '{{ locs.conf_dir }}/profile' '{{bashrc}}' '{{bashprofile}}'|egrep -v "^#"|wc -l)" -lt "4" ]];then
                . '{{ locs.conf_dir }}/profile'
              fi
            fi
    - require_in:
      - file: makina-{{id}}-bashprofile-load

makina-{{id}}-bashprofile-load:
  file.blockreplace:
    - name: {{bashprofile}}
    - marker_start: "# START managed zone profile -DO-NOT-EDIT-"
    - marker_end: "# END managed zone profile"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True

makina-{{id}}-bashrc-load-acc:
  file.accumulated:
    - filename: {{bashrc}}
    - text: |
            if [[ -f '{{bashprofile}}' ]];then
              # only apply if we have no inclusion yet
              if [[ "$(grep -h '.bash_profile' '{{bashrc}}'|egrep -v "^#"|wc -l)" -lt "4" ]];then
                . '{{bashprofile}}'
              fi
            fi
    - require_in:
      - file: makina-{{id}}-bashrc-load

makina-{{id}}-bashrc-load:
  file.blockreplace:
    - name: {{bashrc}}
    - marker_start: "# START managed zone profile -DO-NOT-EDIT-"
    - marker_end: "# END managed zone profile"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
{% endfor %}
