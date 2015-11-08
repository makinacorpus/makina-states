include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set pkgs = salt['mc_pkgs.settings']() %}
{%- set burp = salt['mc_burp.settings']() %}
{%- set udist = 'precise' %}

{% set mode = '' %}
{% if grains['os'] in ['Ubuntu'] %}
{% set mode = 'ppa' %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% if grains['osrelease'][0] < '6' %}
{% set mode = 'debsource' %}
{% endif %}
{% endif %}

{% if mode == 'debsource' %}
installburp:
  file.managed:
    - name: /usr/bin/install-burp.sh
    - source: salt://makina-states/files/usr/bin/install-burp.sh
    - mode: 750
    - user: root
    - watch:
      - mc_proxy: burp-pre-install-hook
  cmd.run:
    - watch:
      - file: installburp
    - name: /usr/bin/install-burp.sh "{{burp.ver}}"
    - stateful: true
    - mode: 750
    - user: root
    - watch_in:
      - mc_proxy: burp-post-install-hook
{% elif mode == 'ppa' %}
burp-repo:
  pkgrepo.managed:
    - humanname: burp {{udist}} stable ppa
    - name: deb http://ppa.launchpad.net/bas-dikkenberg/burp-stable/ubuntu {{udist}}  main
    - file: {{locs.conf_dir}}/apt/sources.list.d/burp.list
    - keyid: 31287BA1
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: install-burp-pkg
{% endif %}
{% if not mode == 'debsource' %}
install-burp-pkg:
#  pkg.{{pkgs['installmode']}}:
  pkg.latest:
    - watch:
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - mc_proxy: burp-post-install-hook
    - pkgs:
      - librsync-dev
      - zlib1g-dev
      - libssl-dev
      - uthash-dev
      - rsync
      - build-essential
      - libncurses5-dev
      - libacl1-dev
{% if grains['os'] in ['Ubuntu'] %}
      - burp
{% endif %}
{% if grains['os'] in ['Debian'] %}
install-burp-pkg2:
#  pkg.{{pkgs['installmode']}}:
  pkg.latest:
    - fromrepo: sid
    - require:
      - pkg: install-burp-pkg
    - pkgs:
      - burp
    - watch:
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - mc_proxy: burp-post-install-hook
{% endif %}
{% endif %}
{% endif %}
# vim:set nofoldenable:
