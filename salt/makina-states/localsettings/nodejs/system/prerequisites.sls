{#
# nodejs configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/nodejs.rst
#}
{% set pkgsettings = salt['mc_pkgs.settings']()%}
{% set locs = salt['mc_locations.settings']()%}
{% set settings = salt['mc_nodejs.settings']()%}
include:
  - makina-states.localsettings.nodejs.hooks
{%  if grains['os'] in ['Ubuntu'] -%}
{#- NODEJS didnt land in LTS, so use the ppa
# https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#ubuntu-mint-elementary-os
# We also install the official binaries inside /srv/app/nodejs/<ver>
#}
nodejs-repo-old:
  file.absent:
    - names:
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejs.list"
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejsn.list"
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejs_a.list"
      - "{{locs.conf_dir}}/apt/sources.list.d/nodejs_b.list"
    - watch_in:
      - mc_proxy: nodejs-post-system-install
nodejs-repo:
  file.absent:
    - name: {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
    - onlyif: |
              set -e
              test -e {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
              grep -qv '{{settings.repo}} ' {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
    - watch:
      - file: nodejs-repo-old
      - mc_proxy: nodejs-pre-system-install
  pkgrepo.managed:
    - name: nodejs
    - humanname: Node.js PPA
    - name: deb https://deb.nodesource.com/{{settings.repo}} {{pkgsettings.dist}} main
    - dist: {{pkgsettings.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/nodejs_c.list
    - key_url: "https://deb.nodesource.com/gpgkey/nodesource.gpg.key"
    - watch:
      - file: nodejs-repo
      - mc_proxy: nodejs-pre-system-install
{% endif %}
nodejs-pkgs-prereqs:
  pkg.{{pkgsettings['installmode']}}:
    - watch:
      - mc_proxy: nodejs-pre-system-install
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - pkgs:
      - wget
      - curl
nodejs-pkgs:
  pkg.latest:
    - watch:
      - pkg: nodejs-pkgs-prereqs
      - mc_proxy: nodejs-pre-system-install
      {% if grains['os'] in ['Ubuntu'] %}
      - pkgrepo: nodejs-repo
      {% endif %}
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - pkgs:
      - nodejs
