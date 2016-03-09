{%- set locs = salt['mc_locations.settings']()%}
{%- set settings = salt['mc_casperjs.settings']() %}
include:
  - makina-states.localsettings.phantomjs.hooks
  - makina-states.localsettings.casperjs.hooks
{#- Install specific versions of casperjs/casperjs  #}
{% macro install(version, dest, hash=None, suf='manual') %}
{% set bn = "casperjs-{0}".format(version, settings.arch) %}
{% set url = settings.url.format(version, settings.arch) %}
{% set archive = url.split('/')[-1] %}
{% set dest = '{0}/{1}'.format(settings['location'], version) %}
casperjs-version-pkgs-{{version.replace('.', '_') }}{{suf}}:
  pkg.installed:
    - pkgs:
      - libfreetype6-dev
      - libfreetype6
      - libfontconfig1-dev
      - fontconfig
    - watch:
      - mc_proxy: casperjs-pre-install
      - mc_proxy: phantomjs-post-install
    - watch_in:
      - mc_proxy: casperjs-post-install
casperjs-version-{{version.replace('.', '_') }}{{suf}}:
  file.directory:
    - name: {{ settings.location }}
    - user: root
    - mode: 755
    - watch:
      - mc_proxy: casperjs-pre-install
      - pkg: casperjs-version-pkgs-{{version.replace('.', '_') }}{{suf}}
    - watch_in:
      - mc_proxy: casperjs-post-install
  archive.extracted:
    - name: {{dest}}
    - if_missing: {{dest}}/bin/.casperjs_{{version}}
    - source: {{url}}
    - archive_format: tar
    {% if archive in settings.shas %}
    {%  set hash = settings.shas[archive]%}
    {% endif %}
    - source_hash: md5={{hash}}
    - watch:
      - file: casperjs-version-{{version.replace('.', '_')}}{{suf}}
    - watch_in:
      - mc_proxy: casperjs-post-install
  cmd.run:
    - name: mv -vf "{{dest}}/{{bn}}/"* "{{dest}}";rm -rf "{{dest}}/{{bn}}/"
    - onlyif: test -e "{{dest}}/{{bn}}"
    - user: root
    - watch:
      - archive: casperjs-version-{{version.replace('.', '_')}}{{suf}}
    - watch_in:
      - mc_proxy: casperjs-post-install
casperjs-version-{{ version.replace('.', '_')}}.post{{suf}}:
  file.touch:
     - name: {{dest}}/bin/.casperjs_{{version}}
     - require:
       - cmd: casperjs-version-{{ version.replace('.', '_') }}{{suf}}
     - watch_in:
       - mc_proxy: casperjs-post-install

{% if suf == 'auto' %}
casperjs-version-{{ version.replace('.', '_')}}.link{{suf}}:
  file.symlink:
    - name: /usr/local/bin/casperjs
    - target: "{{dest}}/bin/casperjs"
    - require:
      - file: casperjs-version-{{ version.replace('.', '_')}}.post{{suf}}
    - watch_in:
      - mc_proxy: casperjs-post-install
{% endif %}
{% endmacro %}
{% for version in settings.versions %}
{{ install(version, suf='auto') }}
{% endfor %}
