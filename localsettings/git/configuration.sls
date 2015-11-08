{#-
# Git configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/git.rst
#}
{% set usersettings = salt['mc_usergroup.settings']() %}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{{ salt['mc_macros.register']('localsettings', 'git') }}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.users
  - makina-states.localsettings.git.hooks
{#
{%- for i, data in usersettings.users.items() %}
{%- set home = data['home'] %}
gitorious_base_ssh_configs-group-{{ i }}:
  file.directory:
    - name: {{ home }}/.ssh
    - mode: 0700
    - user: {{ i }}
    - makedirs: True
    - require:
      - user: {{ i }}

gitorious_base_ssh_configs-touch-{{ i }}:
  file.touch:
    - name: {{ home }}/.ssh/config
    - require:
      - file: gitorious_base_ssh_configs-group-{{ i }}

gitorious_base_ssh_configs-append-{{ i }}:
  file.append:
    - require:
      - file: gitorious_base_ssh_configs-touch-{{ i }}
    - name : {{ home }}/.ssh/config
    - text: |
            # entry managed via salt !
            host=    gitorious.makina-corpus.net
            HostName=gitorious.makina-corpus.net
            Port=2242
{%- endfor %}
#}
global-git-config:
  file.managed:
    - name: {{ locs.conf_dir }}/gitconfig
    - source: salt://makina-states/files/etc/gitconfig
    - mode: 755
    - template: jinja
    - watch_in:
      - mc_proxy: install-recent-git-post
{% endif %}

{% if grains['oscodename'] in ['precise'] %}
git-recent-base:
  pkgrepo.managed:
    - humanname: git ppa
    - name: deb http://ppa.launchpad.net/git-core/ppa/ubuntu {{grains['oscodename']}} main
    - dist: {{grains['oscodename']}}
    - file: /etc/apt/sources.list.d/git.list
    - keyid: E1DF1F24
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: install-recent-git-pre

git-recent-pkgs:
  pkg.latest:
    - pkgs:
      - git
    - watch:
      - mc_proxy: install-recent-git-pre
      - pkgrepo: git-recent-base
    - watch_in:
      - mc_proxy: install-recent-git-post
{% endif %}
