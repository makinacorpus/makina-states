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

{% set locs = salt['mc_locations.settings']() %}
{% set usergroup = salt['mc_usergroup.settings']() %}
{% macro create_user(id, udata) %}
{%- set password = udata.get('password', False) %}
{%- set home = udata['home'] %}
{%- set bashrc = home + '/.bashrc' %}
{%- set bashprofile = home + '/.bash_profile' %}
{{id}}-homes:
  file.directory:
    - names:
      - {{locs.users_home_dir}}
      - {{home}}
    - makedirs: true
    - user: root
    - group: root
    - mode: 755

{{ id }}:
  group.present:
    - name: {{ id }}
    - system: {{udata.system}}
  file.directory:
    - require:
      - file: {{ id }}-homes
    - name: {{ home }}
    - mode: 751
    - makedirs: true
    - user: root
    - group: root
  user.present:
    {% if 'system' in udata %}
    - system: {{udata.system}}
    {% endif %}
    - require:
      - group: {{ id }}
      - file: {{ id }}
    - require_in:
      - mc_proxy: users-ready-hook
    - name: {{ id }}
    {%- if id not in ['root'] %}
    {% if not salt['mc_localsettings.registry']()['is']['ldap'] %}
    - fullname: {{ id }} user
    {% endif %}
    - createhome: True
    - shell: /bin/bash
    - home: {{ home }}
    {# do not change main group when using nssldap #}
    {% if not salt['shadow.info'](id).get('name', '') %}
    - gid_from_name: True
    {% endif %}
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
      {% for g in udata.groups %}
      - {{g}}
      {% endfor %}
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

give-home-{{ id }}:
  file.directory:
    - require:
      - user: {{id}}
      - group: {{id}}
    - name: {{ home }}
    - mode: 751
    - makedirs: true
    - user: {{id}}
    - group: {{id}}

{% if udata['ssh_absent_keys'] %}
{% for key, data in udata['ssh_absent_keys'].items() %}
{% set enc = data.get('encs', ['ed25519, ecdsa', 'ssh-rsa', 'ssh-ds']) %}
{% for enc in encs %}
ssh_auth-absent-key-{{id}}-{{key-}}-ssh-keys:
  ssh_auth.absent:
    - name: '{{key}}'
    - user: {{id}}
    - enc; {{enc}}
    {% for opt in ['options', 'config'] %}
    {% if opt in data %}- {{opt}}: {{data[opt]}}{%endif%}
    {% endfor %}
    - require:
      - user: {{id}}
      - file: {{id}}
{%    endfor %}
{%    endfor %}
{% endif %}

{% if udata['ssh_keys'] %}
ssh_{{id}}-auth-key-cleanup-ssh-keys:
  file.absent:
    - names:
      {#- {{home}}/.ssh/authorized_keys#} {# we do not implicitly remove access, harmful #}
      - {{home}}/.ssh/authorized_keys2
    - require:
      - user: {{id}}
      - file: {{id}}
{% for key in udata['ssh_keys'] %}
ssh_auth-key-{{id}}-{{key-}}-ssh-keys:
  ssh_auth.present:
    - user: {{id}}
    - source: {{key}}
    - require:
      - user: {{id}}
      - file: ssh_{{id}}-auth-key-cleanup-ssh-keys
      - file: {{id}}
{%    endfor %}
{% endif %}

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
{% if salt['mc_controllers.mastersalt_mode']() %}
{% for id, udata in usergroup.users.items() %}
{{ create_user(id, udata) }}
{% endfor %}
{# manage sudoers
{% for i in usergroup.sudoers %}
ms-add-user-{{i}}-to-sudoers:
  user.present:
    - require:
      - mc_proxy: users-ready-hook
    - name: {{i}}
    - home: salt['mc_usergroup.get_home'].get(user)
    - remove_groups: False
    - optional_groups:
      - sudo
{% endfor %}
#}
{% endif %}
{% endmacro %}
{{ do(full=False) }}

