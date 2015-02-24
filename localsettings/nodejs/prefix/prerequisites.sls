{%- set locs = salt['mc_locations.settings']()%}
{%- set settings = salt['mc_nodejs.settings']() %}
include:
  - makina-states.localsettings.nodejs.hooks
{#- Install specific versions of nodejs/npm  #}
{% macro install(version, dest=None, hash=None, suf='manual', source_install=False) %}
{% if grains['cpuarch'] == "x86_64" %}
{% set arch = "x64" %}
{% else %}
{% set arch = "x86" %}
{% endif %}

{% set base_url = "http://nodejs.org/dist/v{v}/{a}" %}

{% if version[:4] in ['0.1.', '0.2.', '0.3.', '0.4.', '0.5.'] %}
{% set base_url= "http://nodejs.org/dist/{a}" %}
{% set source_install=True %}
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
    - watch:
      - archive: npm-version-{{version.replace('.', '_')}}{{suf}}
  {% else %}
  cmd.run:
    - name: mv -vf "{{dest}}/{{bn}}/"* "{{dest}}";rm -rf "{{dest}}/{{bn}}/"
    - onlyif: test -e "{{dest}}/{{bn}}"
    - user: root
    - watch_in:
      - mc_proxy: nodejs-post-prefix-install
    - watch:
      - archive: npm-version-{{version.replace('.', '_')}}{{suf}}
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
