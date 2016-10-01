{%- set locs = salt['mc_locations.settings']()%}
{%- set settings = salt['mc_nodejs.settings']() %}
include:
  - makina-states.localsettings.nodejs.hooks
{#- Install specific versions of nodejs/npm  #}
{% macro install(version, dest=None, hash=None, suf='manual', binary=True, arch=None,
                 source_install=False, manual_npm=False, npm_ver='master') %}

{% if source_install %}{% set binary = False %}{% endif %}
{% if version[:4] in ['0.1.', '0.2.', '0.3.', '0.4.', '0.5.'] %}
{% set manual_npm = True %}
{% set npm_ver='1.0.106' %}
{% endif %}

{% if not dest %}
{% set dest = '{0}/{1}'.format(settings['location'], version) %}
{% endif %}
{% if dest.endswith('/') %}
{% set dest = dest[:-1] %}
{% endif %}

{% set arch = salt['mc_nodejs.get_arch'](arch=arch) %}
{% set url = salt['mc_nodejs.get_url'](version=version, binary=binary, arch=arch) %}
{% set archive = url.split('/')[-1] %}
{% set bn = archive.split('.tar')[0] %}

npm-version-{{version.replace('.', '_') }}{{suf}}:
  file.directory:
    - names: {{ salt['mc_utils.uniquify']([
        '/'.join(dest.split('/')[:-1]),
        '/'.join(dest.split('/')[:-2])]) }}
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
    {% if "xz" in url %}
    - tar_options: J
    {% endif %}
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
{% set installer = '/sbin/npm_install.sh' %}
{% set tag = npm_ver %}
{% if npm_ver not in ['master']%}
{% set tag = 'v{0}'.format(npm_ver) %}
{% endif %}
npm-install-version-{{ version.replace('.', '_')}}.post{{suf}}:
  file.managed:
    - name: "{{installer}}"
    - source: salt://makina-states/files{{installer}}
    - template: jinja
    - user: root
    - defaults:
    - group: root
    - mode: 700
  cmd.run:
    - name: "{{installer}}"
    - user: root
    - unless: test -e "{{dest}}/bin/npm" && test "x$("{{dest}}"/bin/node "{{dest}}"/bin/npm --version)" = "x{{npm_ver}}"
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
