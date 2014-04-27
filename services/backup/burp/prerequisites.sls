include:
  - makina-states.services.backup.burp.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set pkgs = salt['mc_pkgs.settings']() %}
{%- set udist = 'precise' %}
{% if grains['os'] in ['Ubuntu'] %}
burp-repo:
  pkgrepo.managed:
    - humanname: burp {{udist}} stable ppa
    - name: deb http://ppa.launchpad.net/bas-dikkenberg/burp-stable/ubuntu {{udist}}  main
    - consolidate: true
    - file: {{locs.conf_dir}}/apt/sources.list.d/burp.list
    - keyid: 31287BA1
    - keyserver: keyserver.ubuntu.com
{% endif %}
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
    - require:
      - pkgrepo: burp-repo
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
# vim:set nofoldenable:
