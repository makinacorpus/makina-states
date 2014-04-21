include:
  - makina-states.services.backup.burp.hooks
{%- set locs = salt['mc_locations.settings']() %}
{%- set pkgs = salt['mc_pkgs.settings']() %}
{%- set udist = pkgs.udist %}
deadsnakes:
  pkgrepo.managed:
    - humanname: burp stable ppa
    - name: deb http://ppa.launchpad.net/bas-dikkenberg/burp-stable/ubuntu {{udist}} main
    - dist: {{udist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/burp.list
    - keyid: 31287BA1
    - keyserver: keyserver.ubuntu.com
  pkg.{{pkgs['installmode']}}:
    - require:
      - pkgrepo: deadsnakes
    - pkgs:
      - burp
      - librsync-dev
      - libz-dev
      - libssl-dev
      - uthash-dev
      - rsync
      - build-essential
      - libncurses5-dev
      - libacl1-dev
    - watch:
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - mc_proxy: burp-post-install-hook
# vim:set nofoldenable: 
