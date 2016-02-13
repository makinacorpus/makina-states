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
{% macro create_user(id, udata=None) %}
{%- if not udata %}{%- set udata = {} %}{%endif%}
{%- set ssk_keys = udata.setdefault('ssh_keys', []) %}
{%- set ssk_absent_keys = udata.setdefault('ssh_absent_keys', []) %}
{%- set ugroup = udata.setdefault('group', id) %}
{%- set groups = udata.setdefault('groups', []) %}
{%- set system = udata.setdefault('system', False) %}
{%- set password = udata.setdefault('password', False) %}
{%- set home = udata.setdefault('home', '/home/users/{0}'.format(id)) %}
{%- set bashrc = home + '/.bashrc' %}
{%- set bashprofile = home + '/.bash_profile' %}
{{id}}-homes:
  file.directory:
    - names:
      - {{locs.users_home_dir}}
    - makedirs: true
    - user: root
    - group: root
    - mode: "0755"

{{ id }}:
  group.present:
    - name: {{ ugroup }}
    - system: {{system}}
  user.present:
    - system: {{system}}
    - require:
      - group: {{ id }}
    - require_in:
      - mc_proxy: users-ready-hook
    - name: {{ id }}
    {%- if password %}
    - enforce_password: True
    - password:  {{ password }}
    {%- endif %}
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
  file.directory:
    - require:
      - file: {{ id }}-homes
      - group: {{ id }}
      - user: {{ id }}
    - name: {{ home }}
    - mode: 751
    - makedirs: true
    - user: "{{id}}"
    - group: "{{id}}"

give-home-{{ id }}:
  file.directory:
    - require:
      - user: {{id}}
      - group: {{id}}
    - watch_in:
      - mc_proxy: users-ready-hook
    - name: {{ home }}
    - mode: 751
    - makedirs: true
    - user: {{id}}
    - group: {{id}}

{% if udata['ssh_absent_keys'] %}
{% for rkeydata in udata['ssh_absent_keys'] %}
{% for key, data in rkeydata.items() %}
{% set encs = data.get('encs', ['ed25519', 'ecdsa', 'ssh-rsa', 'ssh-ds']) %}
{% for enc in encs %}
ssh_auth-absent-key-{{id}}-{{key}}-{{loop.index0-}}-ssh-keys:
  ssh_auth.absent:
    - name: '{{key}}'
    - user: {{id}}
    - enc: {{enc}}
    {% for opt in ['options', 'config'] %}
    {% if opt in data %}- {{opt}}: {{data[opt]}}{%endif%}
    {% endfor %}
    - require:
      - user: {{id}}
      - file: {{id}}
{%    endfor %}
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
{% if key.endswith('.pub') and '/files/' in key %}
ssh_auth-key-{{id}}-{{key-}}-ssh-keys:
{% else%}
ssh_auth-key-{{id}}-keys-{{loop.index0}}-ssh-keys:
{% endif %}
  ssh_auth.present:
    - user: {{id}}
    {% if key.endswith('.pub') and '/files/' in key %}
    - source: {{key}}
    {% else%}
    - name: '{{key}}'
    {% endif %}
    - require:
      - user: {{id}}
      - file: ssh_{{id}}-auth-key-cleanup-ssh-keys
      - file: {{id}}
{%    endfor %}
{% endif %}

makina-{{id}}-bashfiles:
  file.managed:
    - names:
        - {{bashrc}}
        - {{bashprofile}}
    - source: ''
    - user: "{{id}}"
    - mode: 755
    - group: "{{id}}"
    - require:
      - file: {{id}}
    - require_in:
      - file: makina-{{id}}-bashprofile-load
      - mc_proxy: users-ready-hook

makina-{{id}}-bashprofile-load-acc:
  file.accumulated:
    - filename: {{bashprofile}}
    - text: |
            USERENV="$(echo $(whoami)_${$}|sed -e "s/\(-\)//g")"
            if [ -f '{{ locs.conf_dir }}/profile' ];then
              # only apply if we have no inclusion yet
              if [ "x$(env|grep -q "${USERENV}_BASH_RC_PROFILE_LOADED";echo ${?})" = "x1" ];then
                export "${USERENV}_BASH_RC_PROFILE_LOADED"="1"
                . '{{ locs.conf_dir }}/profile'
              fi
            fi
            if [ -e '{{bashrc}}' ];then
              # only apply if we have no inclusion yet
              if [ "x$(env|grep -q "${USERENV}_BASH_RC_LOADED";echo ${?})" = "x1" ];then
                export "${USERENV}_BASH_RC_LOADED"="1"
                . '{{bashrc}}'
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
            # ~/.bashrc: executed by bash(1) for non-login shells.
            # see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
            # for examples
            #only load once, we are on a slot, test if we do not have this content on the complete file
            if [ "$(grep lesspipe "{{bashrc}}"|wc -l|sed -e "s/ //g")" -lt "4" ];then
              # If not running interactively, don't do anything
              [ -z "$PS1" ] && return
              # ... or force ignoredups and ignorespace
              HISTCONTROL=ignoredups:ignorespace
              # append to the history file, don't overwrite it
              shopt -s histappend
              # for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
              HISTSIZE=1000
              HISTFILESIZE=2000
              # check the window size after each command and, if necessary,
              # update the values of LINES and COLUMNS.
              shopt -s checkwinsize
              # make less more friendly for non-text input files, see lesspipe(1)
              [ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"
              # set variable identifying the chroot you work in (used in the prompt below)
              if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
                  debian_chroot=$(cat /etc/debian_chroot)
              fi
              # set a fancy prompt (non-color, unless we know we "want" color)
              case "$TERM" in
                  xterm-color) color_prompt=yes;;
              esac
              # uncomment for a colored prompt, if the terminal has the capability; turned
              # off by default to not distract the user: the focus in a terminal window
              # should be on the output of commands, not on the prompt
              #force_color_prompt=yes
              if [ -n "$force_color_prompt" ]; then
                  if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
                # We have color support; assume it's compliant with Ecma-48
                # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
                # a case would tend to support setf rather than setaf.)
                color_prompt=yes
                  else
                color_prompt=
                  fi
              fi
              if [ "$color_prompt" = yes ]; then
                  PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
              else
                  PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
              fi
              unset color_prompt force_color_prompt

              # If this is an xterm set the title to user@host:dir
              case "$TERM" in
              xterm*|rxvt*)
                  PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
                  ;;
              *)
                  ;;
              esac
              # enable color support of ls and also add handy aliases
              if [ -x /usr/bin/dircolors ]; then
                  test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
                  alias ls='ls --color=auto'
                  #alias dir='dir --color=auto'
                  #alias vdir='vdir --color=auto'
                  alias grep='grep --color=auto'
                  alias fgrep='fgrep --color=auto'
                  alias egrep='egrep --color=auto'
              fi
              # some more ls aliases
              alias ll='ls -alF'
              alias la='ls -A'
              alias l='ls -CF'
              # Alias definitions.
              # You may want to put all your additions into a separate file like
              # ~/.bash_aliases, instead of adding them here directly.
              # See /usr/share/doc/bash-doc/examples in the bash-doc package.
              if [ -f ~/.bash_aliases ]; then
                  . ~/.bash_aliases
              fi
              # enable programmable completion features (you don't need to enable
              # this, if it's already enabled in /etc/bash.bashrc and /etc/profile
              # sources /etc/bash.bashrc).
              #if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
              #    . /etc/bash_completion
              #fi
            fi
            ############
            USERENV="$(echo $(whoami)_${$}|sed -e "s/\(-\)//g")"
            if [ -f '{{bashprofile}}' ];then
              # only apply if we have no inclusion yet
              if [ "x$(env|grep -q "${USERENV}_BASH_PROFILE_LOADED";echo ${?})" = "x1" ];then
                export ${USERENV}_BASH_PROFILE_LOADED="1"
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
{% set add_user = create_user %}

include:
  # too dangerous to not keep the sync state not in sync with users
  - makina-states.localsettings.shell
  - makina-states.localsettings.users.hooks
  - makina-states.localsettings.groups
  - makina-states.localsettings.sudo
{{ salt['mc_macros.register']('localsettings', 'users') }}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
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

