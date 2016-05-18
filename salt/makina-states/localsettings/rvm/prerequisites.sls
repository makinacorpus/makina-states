{%- set rvms = salt['mc_rvm.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}

include:
 - makina-states.localsettings.rvm.hooks

rvm-deps:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
   - pkgs:
     {% for i in rvms.pkgs %}
     - {{i}}
     {% endfor %}
   - require:
     - mc_proxy: rvm-install-pre
   - require_in:
     - mc_proxy: rvm-install-post


{{rvms.group}}-group:
  group.present:
    - name: {{rvms.group}}
    - require:
      - mc_proxy: rvm-install-pre
    - require_in:
      - mc_proxy: rvm-install-post

{{rvms.user}}-user:
  user.present:
    - name: {{rvms.user}}
    - gid: {{rvms.group}}
    - home: /home/rvm
    - require:
      - mc_proxy: rvm-install-pre
      - group: {{rvms.group}}
    - require_in:
      - mc_proxy: rvm-install-post

rvm-dir:
 file.directory:
    - name: {{locs.rvm_path}}
    - group: {{rvms.group}}
    - user: {{rvms.user}}
    - require:
      - mc_proxy: rvm-install-pre
      - user: {{rvms.user}}
      - group: {{rvms.group}}
    - require_in:
      - mc_proxy: rvm-install-post

rvm-setup:
  cmd.run:
    - name: |
            cd /tmp
            wget -O rvm-installer "{{rvms.url}}"
            chmod +x rvm-installer
            curl -sSL https://rvm.io/mpapis.asc | gpg --import -
            ./rvm-installer {{rvms.branch}} && {{locs.rvm}} fix-permissions
    - use_vt: true
    - unless: test -e {{locs.rvm_path}}/bin/rvm
    - require:
      - mc_proxy: rvm-install-pre
      - pkg: rvm-deps
      - file: rvm-dir
      - user:  {{rvms.user}}-user
    - require_in:
      - mc_proxy: rvm-install-post

