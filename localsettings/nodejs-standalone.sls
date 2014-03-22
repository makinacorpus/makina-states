{#-
# nodejs configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/nodejs.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{%- set locs = salt['mc_localsettings']()['locations'] %}

{% macro npmInstall(npmPackage, npmVersion="system") %}
npm-packages-{{npmPackage}}:
  cmd.run:
    {% if npmVersion == "system" %}
    - name: npm install -g {{npmPackage}}
    {% else %}
    - name: |
            export PATH={{ locs['apps_dir'] }}/nodejs/{{ npmVersion }}/bin:$PATH;
            if [ ! -e {{ locs['apps_dir'] }}/nodejs/{{ npmVersion }}/bin/npm ];
            then exit 1;
            else npm install -g {{npmPackage}};
            fi
    {% endif %}
{% endmacro %}

{% macro do(full=True) %}
{{ salt['mc_macros.register']('localsettings', 'nodejs') }}
{%- set npmPackages = localsettings.npmSettings.packages %}
{% if full %}
include:
  - makina-states.localsettings.pkgmgr
  - makina-states.localsettings.pkgs
{% endif %}

{% if full %}
{%  if grains['os'] in ['Ubuntu'] -%}
{#- NODEJS didnt land in LTS, so use the ppa
# https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#ubuntu-mint-elementary-os
#}
nodejs-repo:
  pkgrepo.managed:
    - name: nodejs
    - humanname: Node.js PPA
    - name: deb http://ppa.launchpad.net/chris-lea/node.js/ubuntu {{localsettings.dist}} main
    - dist: {{localsettings.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/nodejs.list
    - keyid: C7917B12
    - keyserver: keyserver.ubuntu.com
    - require:
        - file: apt-sources-list
        - cmd: apt-update-after
        - pkg: net-pkgs
{%  endif %}
nodejs-pkgs:
  pkg.{{localsettings.installmode}}:
    {% if grains['os'] in ['Ubuntu'] -%}
    - require:
      - pkgrepo: nodejs-repo
    {%- endif %}
    - pkgs:
      - nodejs

{%  if grains['os'] in ['Debian'] -%}
npm-pkgs:
  file.symlink:
    - target: {{locs.bin_dir}}/nodejs
    - name:   {{locs.bin_dir}}/node
  cmd.run:
    - unless: which npm
    - name: |
            . /etc/profile &&
            curl -s https://npmjs.org/install.sh -o /tmp/npminstall &&
            chmod +x /tmp/npminstall &&
            /tmp/npminstall && rm -f /tmp/npminstall;
    - require:
      - file: npm-pkgs
      - pkg: nodejs-pkgs
{%-   endif %}

{#- Install specific versions of npm  #}
{% if grains['cpuarch'] == "x86_64" %}
{% set arch = "x64" %}
{% else %}
{% set arch = "x86" %}
{% endif %}

{% for version in localsettings.npmSettings.versions %}
{% set archive = "node-v"+ version +"-linux-"+ arch  %}
npm-version-{{ version }}:
  file.directory:
    - name: {{ locs['apps_dir'] }}/nodejs
  cmd.run:
    - unless: ls -d {{ locs['apps_dir'] }}/nodejs/{{ version }}
    - cwd: {{ locs['apps_dir'] }}/nodejs
    - name: |
            wget http://nodejs.org/dist/v{{ version }}/{{ archive }}.tar.gz &&
            tar xzvf {{ archive }}.tar.gz &&
            mv {{ archive }} {{ version }}
{% endfor %}
{% endif %}

{% for npmPackage in npmPackages -%}
{{ npmInstall(npmPackage) }}
{%- endfor %}

{% endmacro %}
{{ do(full=False)}}
