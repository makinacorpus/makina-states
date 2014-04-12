{#
# nodejs configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/nodejs.rst
#}
{% set pkgsettings = salt['mc_pkgs.settings']()%}
{% set locs = salt['mc_locations.settings']()%}
include:
  - makina-states.localsettings.nodejs.hooks
{%  if grains['os'] in ['Ubuntu'] -%}
{#- NODEJS didnt land in LTS, so use the ppa
# https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#ubuntu-mint-elementary-os
# We also install the official binaries inside /srv/app/nodejs/<ver>
#}
nodejs-repo:
  pkgrepo.managed:
    - name: nodejs
    - humanname: Node.js PPA
    - name: deb http://ppa.launchpad.net/chris-lea/node.js/ubuntu {{pkgsettings.dist}} main
    - dist: {{pkgsettings.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/nodejs.list
    - keyid: C7917B12
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: nodejs-pre-system-install
{% endif %}
nodejs-pkgs:
  pkg.{{pkgsettings['installmode']}}:
    - watch:
      - mc_proxy: nodejs-pre-system-install
      {% if grains['os'] in ['Ubuntu'] %}
      - pkgrepo: nodejs-repo
      {% endif %}
    - watch_in:
      - mc_proxy: nodejs-post-system-install
    - pkgs:
      - wget
      - curl
      {% if grains['os'] in ['Ubuntu'] %}
      - nodejs
      {% endif %}
