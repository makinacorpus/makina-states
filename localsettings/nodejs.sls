#
# Install Node.js and allow the installation of Node.js packages through npm
#
# You can use the grain/pillar following setting to select the npm packages:
# makina-states.localsettings.npm_packages: LIST (default: [])
#
# You can include version, eg:
# makina-states.localsettings.npm_packages: ['grunt@0.6']
#

{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% set locs = localsettings.locations %}
{{ localsettings.register('nodejs') }}

{% set npm_packages = salt['mc_utils.get'](
   'makina-states.localsettings.npm_packages',
   []) %}

{% if grains['os'] in ['Ubuntu'] %}
# Installing the last version of Node: https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#ubuntu-mint-elementary-os
nodejs:
  pkgrepo.managed:
    - humanname: Node.js PPA
    - name: deb http://ppa.launchpad.net/chris-lea/node.js/ubuntu {{udist}} main
    - dist: {{udist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/nodejs.list
    - keyid: C7917B12
    - keyserver: keyserver.ubuntu.com
  pkg.installed:
    - require:
      - pkgrepo: nodejs
    - pkgs:
      - nodejs
      - npm

npm-packages:
  {% for npm_package in npm_packages %}
  {{npm_package}}:
    npm:
      - installed
  {% endfor %}
{% endif %}