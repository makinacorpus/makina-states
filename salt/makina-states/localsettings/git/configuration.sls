{#- # Git configuration #}
{% set usersettings = salt['mc_usergroup.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'git') }}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.git.hooks
global-git-config:
  file.managed:
    - name: {{ locs.conf_dir }}/gitconfig
    - source: salt://makina-states/files/etc/gitconfig
    - mode: 755
    - template: jinja
    - watch_in:
      - mc_proxy: install-recent-git-post
{% if grains['oscodename'] in ['precise'] %}
git-recent-base:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
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