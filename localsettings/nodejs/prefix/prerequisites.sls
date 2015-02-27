{%- set locs = salt['mc_locations.settings']()%}
{%- set settings = salt['mc_nodejs.settings']() %}
include:
  - makina-states.localsettings.nodejs.hooks
{#- Install specific versions of nodejs/npm  #}
{% macro install(version, dest=None, hash=None, suf='manual', source_install=False, manual_npm=False, npm_ver='master') %}
{% if grains['cpuarch'] == "x86_64" %}
{% set arch = "x64" %}
{% else %}
{% set arch = "x86" %}
{% endif %}

{% set base_url = "http://nodejs.org/dist/v{v}/{a}" %}

{% if version[:4] in ['0.1.', '0.2.', '0.3.', '0.4.', '0.5.'] %}
{% set base_url= "http://nodejs.org/dist/{a}" %}
{% set source_install=True %}
{% set manual_npm = True %}
{% set npm_ver='1.0.106' %}
{% endif %}

{% if not dest %}
{% set dest = '{0}/{1}'.format(settings['location'], version) %}
{% endif %}
{% if dest.endswith('/') %}
{% set dest = dest[:-1] %}
{% endif %}

{% set bn = "node-v{0}-linux-{1}".format(version, arch) %}

{% if source_install %}
{% set archive = "node-v{v}.tar.gz".format(v=version)   %}
{% else %}
{% set archive = "{0}.tar.gz".format(bn)   %}
{% endif %}

{% set url = base_url.format(a=archive, v=version) %}

npm-version-{{version.replace('.', '_') }}{{suf}}:
  file.directory:
    - name: {{ '/'.join(dest.split('/')[:-1]) }}
    - makedirs: true
    - user: root
    - mode: 755
    - watch:
      - mc_proxy: nodejs-pre-prefix-install
  archive.extracted:
    - name: {{dest}}
    - if_missing: {{dest}}/bin/.node_{{version}}
    - source: {{url}}
    - archive_format: tar
    {% if archive in settings.shas %}
    {%  set hash = settings.shas[archive]%}
    {% endif %}
    - source_hash: sha1={{hash}}
    - watch_in:
      - mc_proxy: nodejs-post-prefix-install
    - watch:
      - file: npm-version-{{version.replace('.', '_')}}{{suf}}
  {% if source_install %}
  cmd.run:
    - name: |
            set -e
            ./configure --prefix="{{dest}}"
            make
            make install
    - cwd: "{{dest}}/node-v{{version}}"
    - use_vt: true
    - unless: test -e "{{dest}}/bin/node"
    - user: root
    - watch_in:
      - mc_proxy: nodejs-post-prefix-install
    {% if manual_npm %}
      - file: npm-install-version-{{ version.replace('.', '_')}}.post{{suf}}
    {% endif %}
    - watch:
      - archive: npm-version-{{version.replace('.', '_')}}{{suf}}
  {% else %}
  cmd.run:
    - name: mv -vf "{{dest}}/{{bn}}/"* "{{dest}}";rm -rf "{{dest}}/{{bn}}/"
    - onlyif: test -e "{{dest}}/{{bn}}"
    - user: root
    - watch_in:
      - mc_proxy: nodejs-post-prefix-install
    {% if manual_npm %}
      - file: npm-install-version-{{ version.replace('.', '_')}}.post{{suf}}
    {% endif %}
    - watch:
      - archive: npm-version-{{version.replace('.', '_')}}{{suf}}
  {% endif %}

{% if manual_npm %}
{% set installer = '/sbin/npm_install_{0}{1}.sh'.format(suf, version) %}
{% set tag = npm_ver %}
{% if npm_ver not in ['master']%}
{% set tag = 'v{0}'.format(npm_ver) %}
{% endif %}
npm-install-version-{{ version.replace('.', '_')}}.post{{suf}}:
  file.managed:
    - name: "{{installer}}"
    - source: salt://makina-states/files/sbin/npm_install.sh
    - template: jinja
    - user: root
    - defaults:
    - group: root
    - mode: 700
  cmd.run:
    - name: "{{installer}}"
    - user: root
    - unless: test -e "{{dest}}/bin/npma" && test "x$("{{dest}}"/bin/node "{{dest}}"/bin/npm --version)" = "x{{npm_ver}}"
    - env:
        NPM_TAG: "{{tag}}"
        NODE: "{{dest}}/bin/node"
    - use_vt: true
    - watch:
      - file: npm-install-version-{{ version.replace('.', '_')}}.post{{suf}}
{% endif %}


npm-version-{{ version.replace('.', '_')}}.post{{suf}}:
  file.touch:
     - name: {{dest}}/bin/.node_{{version}}
     - require:
       - cmd: npm-version-{{ version.replace('.', '_') }}{{suf}}
     - watch_in:
       - mc_proxy: nodejs-post-prefix-install

{% endmacro %}
{% for version in settings.versions %}
{{ install(version, suf='auto') }}
{% endfor %}
