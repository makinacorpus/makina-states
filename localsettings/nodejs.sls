#
# Install Node.js and allow the installation of Node.js packages through npm
#
# You can use the grain/pillar following setting to select the npm packages:
# makina-states.localsettings.npmPackages: LIST (default: [])
#
# You can include version, eg:
# makina-states.localsettings.npmPackages: ['grunt@0.6']
#

{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% set locs = localsettings.locations %}
{{ localsettings.register('nodejs') }}

{% set npmPackages = localsettings.npmPackages %}

{% if grains['os'] in ['Ubuntu'] %}
# Installing the last version of Node: https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#ubuntu-mint-elementary-os
nodejs-repo:
  pkgrepo.managed:
    - name: nodejs
    - humanname: Node.js PPA
    - name: deb http://ppa.launchpad.net/chris-lea/node.js/ubuntu {{localsettings.dist}} main
    - dist: {{localsettings.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/nodejs.list
    - keyid: C7917B12
    - keyserver: keyserver.ubuntu.com

nodejs-pkgs:
  pkg.installed:
    - name: nodejs
    - require:
      - pkgrepo: nodejs-repo
    - pkgs:
      - nodejs

{% for npmPackage in npmPackages %}
npm-packages{{npmPackage}}:
  npm.installed:
    - name: {{npmPackage}}
{% endfor %}
{% endif %}
