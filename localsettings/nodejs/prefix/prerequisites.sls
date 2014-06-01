{%- set locs = salt['mc_locations.settings']()%}
{%- set settings = salt['mc_nodejs.settings']() %}
include:
  - makina-states.localsettings.nodejs.hooks
{#- Install specific versions of nodejs/npm  #}
{% macro install(version, dest, hash=None) %}
{% if grains['cpuarch'] == "x86_64" %}
{% set arch = "x64" %}
{% else %}
{% set arch = "x86" %}
{% endif %}
{% set bn = "node-v{0}-linux-{1}".format(version, arch) %}
{% set archive = "{0}.tar.gz".format(bn)   %}
{% set dest = '{0}/{1}'.format(settings['location'], version) %}
npm-version-{{version.replace('.', '_') }}:
  file.directory:
    - name: {{ settings.location }}
    - user: root
    - mode: 755
    - watch:
      - mc_proxy: nodejs-pre-prefix-install
  archive.extracted:
    - name: {{dest}}
    - if_missing: {{dest}}/bin/.node_{{version}}
    - source: http://nodejs.org/dist/v{{ version }}/{{archive}}
    - archive_format: tar
    {% if archive in settings.shas %}
    {%  set hash = settings.shas[archive]%}
    {% endif %}
    - source_hash: sha1={{hash}}
    - watch_in:
      - mc_proxy: nodejs-post-prefix-install
    - watch:
      - file: npm-version-{{version.replace('.', '_')}}
  cmd.run:
    - name: mv -vf "{{dest}}/{{bn}}/"* "{{dest}}" && rm -rf "{{dest}}/{{bn}}/"
    - onlyif: test -e "{{dest}}/{{bn}}"
    - user: root
    - watch_in:
      - mc_proxy: nodejs-post-prefix-install
    - watch:
      - archive: npm-version-{{version.replace('.', '_')}}
npm-version-{{ version.replace('.', '_')}}.post:
  file.touch:
     - name: {{dest}}/bin/.node_{{version}}
     - require:
       - cmd: npm-version-{{ version.replace('.', '_') }}
{% endmacro %}
{% for version in settings.versions %}
{{ install(version) }}
{% endfor %}
