{#-
# vim configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/users.rst
# to generate a password hash
# USE ``python -c "import crypt, getpass, pwd; print crypt.crypt('password', '\$6\$SALTsalt\$')"``
# or python
# >>> import crypt, getpass, pwd; print crypt.crypt('password', '$6$SALTsalt$')
#
# Idea is to create any user/group needed for ssh managment
#}


{% set localsettings = salt['mc_localsettings.settings']() %}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% macro create_user(id, udata) %}
{%- set password = udata.get('password', False) %}
{%- set home = udata['home'] %}
{%- set bashrc = home + '/.bashrc' %}
{%- set bashprofile = home + '/.bash_profile' %}
{{id}}-homes:
 file.directory:
    - name: {{locs.users_home_dir}}
    - makedirs: true
    - user: root
    - group: root
    - mode: 755

{{ id }}:
  group.present:
    - name: {{ id }}
    - system: True
  user.present:
    - require:
      - group: {{ id }}
    - require_in:
      - mc_proxy: users-ready-hook
    - name: {{ id }}
    {%- if id not in ['root'] %}
    - fullname: {{ id }} user
    - createhome: True
    - shell: /bin/bash
    - home: {{ home }}
    - gid_from_name: True
    - remove_groups: False
    {%- if password %}
    - password:  {{ password }}
    {%- endif %}
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
  file.directory:
    - require:
      - user: {{ id }}
      - file: {{ id }}-homes
    - name: {{ home }}
    - mode: 751
    - makedirs: true
    - user: {{id}}
    - group: {{id}}

{% for key in udata.get('ssh_keys', []) %}
ssh_auth-key-{{id}}-{{key}}:
  ssh_auth.present:
    - user: {{id}}
    - source: salt://files/ssh/{{ key }}
    - require:
      - user: {{id}}
      - file: {{id}}
{%    endfor %}

makina-{{id}}-bashfiles:
  file.touch:
    - names:
        - {{bashrc}}
        - {{bashprofile}}
    - require_in:
      - file: makina-{{id}}-bashprofile-load
    - require:
      - file: {{id}}
  cmd.run:
    - name: >
            chown {{id}}:{{id}} '{{bashrc}}' '{{bashprofile}}';
            chmod 755 '{{bashrc}}' '{{bashprofile}}';
            echo;echo "changed=false comment='do no trigger changes'"
    - stateful: True
    - require:
      - file: makina-{{id}}-bashfiles
    - require_in:
      - file: makina-{{id}}-bashprofile-load
      - mc_proxy: users-ready-hook

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
      - mc_proxy: users-ready-hook
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
    - require_in:
      - mc_proxy: users-ready-hook

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
      - mc_proxy: users-ready-hook

makina-{{id}}-bashrc-load:
  file.blockreplace:
    - name: {{bashrc}}
    - marker_start: "# START managed zone profile -DO-NOT-EDIT-"
    - marker_end: "# END managed zone profile"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
      - file: makina-{{id}}-bashfiles
    - require_in:
      - mc_proxy: users-ready-hook
{% endmacro %}

{% macro do(full=False) %}
include:
  - makina-states.localsettings.users-hooks
  - makina-states.localsettings.groups
  - makina-states.localsettings.sudo
{{ salt['mc_macros.register']('localsettings', 'users') }}
{% for id, udata in localsettings.users.items() %}
{{ create_user(id, udata) }}
{% endfor %}

{#
#}
{# manage sudoers #}
{% for i in localsettings.sudoers %}
ms-add-user-{{i}}-to-sudoers:
  user.present:
    - require:
      - mc_proxy: users-ready-hook
    - name: {{i}}
    - remove_groups: False
    - optional_groups:
      - sudo
{% endfor %}
{% endmacro %}
{{ do(full=False) }}
