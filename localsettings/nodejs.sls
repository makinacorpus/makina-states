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

{% set npmPackages = localsettings.npmSettings.packages %}

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
{% endif %}

{% if grains['os'] in ['Debian'] %}
nodejs-repo:
  pkgrepo.managed:
    - name: nodejs
    - humanname: Node.js wheezy-backports
    - name: deb http://ftp.us.debian.org/debian wheezy-backports main
    - dist: wheezy-backports
    - file: {{locs.conf_dir}}/apt/sources.list.d/nodejs.list

nodejs-pkgs:
  pkg.installed:
    - name: nodejs
    - require:
      - pkgrepo: nodejs-repo
    - pkgs:
      - nodejs-legacy

npm-pkgs:
  cmd.run:
    - name: curl -s https://npmjs.org/install.sh | sh
    - require:
      - pkg: nodejs
{% endif %}

{% for npmPackage in npmPackages %}
npm-packages{{npmPackage}}:
  npm.installed:
    - name: {{npmPackage}}
{% endfor %}
