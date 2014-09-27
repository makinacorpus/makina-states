{%- set locs = salt['mc_locations.settings']()%}
{%- set settings = salt['mc_phantomjs.settings']() %}
include:
  - makina-states.localsettings.phantomjs.hooks
{#- Install specific versions of phantomjs/phantomjs  #}
{% macro install(version, dest, hash=None, suf='manual') %}
{% set bn = settings.bn.format(version, settings.arch) %}
{% set url = settings.url.format(version, settings.arch) %}
{% set archive = url.split('/')[-1] %}
{% set dest = '{0}/{1}'.format(settings['location'], version) %}
phantomjs-version-pkgs-{{version.replace('.', '_') }}{{suf}}:
  pkg.installed:
    - pkgs:
      - libfreetype6-dev
      - libfreetype6
      - libfontconfig1-dev
      - fontconfig
    - watch:
      - mc_proxy: phantomjs-pre-install
    - watch_in:
      - mc_proxy: phantomjs-post-install
phantomjs-version-{{version.replace('.', '_') }}{{suf}}:
  file.directory:
    - name: {{ settings.location }}
    - user: root
    - mode: 755
    - watch:
      - mc_proxy: phantomjs-pre-install
      - pkg: phantomjs-version-pkgs-{{version.replace('.', '_') }}{{suf}}
    - watch_in:
      - mc_proxy: phantomjs-post-install
  archive.extracted:
    - name: {{dest}}
    - if_missing: {{dest}}/bin/.phantomjs_{{version}}
    - source: {{url}}
    - archive_format: tar
    {% if archive in settings.shas %}
    {%  set hash = settings.shas[archive]%}
    {% endif %}
    - source_hash: md5={{hash}}
    - watch:
      - file: phantomjs-version-{{version.replace('.', '_')}}{{suf}}
    - watch_in:
      - mc_proxy: phantomjs-post-install
  cmd.run:
    - name: mv -vf "{{dest}}/{{bn}}/"* "{{dest}}";rm -rf "{{dest}}/{{bn}}/"
    - onlyif: test -e "{{dest}}/{{bn}}"
    - user: root
    - watch:
      - archive: phantomjs-version-{{version.replace('.', '_')}}{{suf}}
    - watch_in:
      - mc_proxy: phantomjs-post-install
phantomjs-version-{{ version.replace('.', '_')}}.post{{suf}}:
  file.touch:
     - name: {{dest}}/bin/.phantomjs_{{version}}
     - require:
       - cmd: phantomjs-version-{{ version.replace('.', '_') }}{{suf}}
     - watch_in:
       - mc_proxy: phantomjs-post-install

{% if suf == 'auto' %}
phantomjs-version-{{ version.replace('.', '_')}}.link{{suf}}:
  file.symlink:
    - name: /usr/local/bin/phantomjs
    - target: "{{dest}}/bin/phantomjs"
    - require:
      - file: phantomjs-version-{{ version.replace('.', '_')}}.post{{suf}}
    - watch_in:
      - mc_proxy: phantomjs-post-install
{% endif %}
{% endmacro %}
{% for version in settings.versions %}
{{ install(version, suf='auto') }}
{% endfor %}
