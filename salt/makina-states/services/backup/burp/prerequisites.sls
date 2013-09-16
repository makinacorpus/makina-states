{% import "makina-states/_macros/h.jinja" as h with context %}
include:
  - makina-states.services.backup.burp.hooks
{%- set locs = salt['mc_locations.settings']() %}
{%- set burp = salt['mc_burp.settings']() %}

{% if burp.ppa %}
burp-repo:
  pkgrepo.managed:
    - humanname: burp stable ppa
    - name: '{{burp.ppa}}'
    - file: {{locs.conf_dir}}/apt/sources.list.d/burp.list
    - keyid: 31287BA1
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - pkg: install-burp-pkg
      - mc_proxy: burp-post-install-hook
{% else %}
burp-repo:
  file.absent:
    - name: {{locs.conf_dir}}/apt/sources.list.d/burp.list
    - watch:
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - pkg: install-burp-pkg
      - mc_proxy: burp-post-install-hook
{% endif %}

install-burp-pkg:
  pkg.latest:
    - pkgs: {{burp.pkgs }}
    {% if burp.fromrepo %}
    - fromrepo: {{ burp.fromrepo }}
    {% endif %}
    - watch:
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - mc_proxy: burp-post-install-hook
{{ h.retry_apt_get(failed_from=['pkg: install-burp-pkg'],
                   pkgs=burp.pkgs, pref='burp',
                   fromrepo=burp.fromrepo)}}
{% if burp.source %}
installburp:
  file.managed:
    - name: /usr/bin/install-burp.sh
    - source: salt://makina-states/files/usr/bin/install-burp.sh
    - mode: 750
    - user: root
    - watch:
      - pkgs: install-burp-pkg
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - mc_proxy: burp-post-install-hook
  cmd.run:
    - name: /usr/bin/install-burp.sh "{{burp.ver}}"
    - stateful: true
    - user: root
    - watch:
      - file: installburp
      - mc_proxy: burp-pre-install-hook
    - watch_in:
      - mc_proxy: burp-post-install-hook
{% endif %}
