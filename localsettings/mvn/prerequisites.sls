{%- set locs = salt['mc_locations.settings']()%}
{%- set settings = salt['mc_mvn.settings']() %}
include:
  - makina-states.localsettings.mvn.hooks
  - makina-states.localsettings.jdk

{% macro install(version,
                 url=None,
                 dest=None,
                 hash=None,
                 suf='manual',
                 link=True) %}

{% if not url %}
{% set url = settings['url'] %}
{% endif %}

{% if not dest %}
{% set dest = '{0}/{1}'.format(settings['location'], version) %}
{% endif %}

{% if dest.endswith('/') %}
{% set dest = dest[:-1] %}
{% endif %}

{% if version in settings.shas and not hash %}
{%  set hash = settings.shas[version]%}
{% endif %}

{% set url = url.format(version=version) %}

{% set sid = '{0}{1}'.format(version.replace('.', '_'), suf) %}
mvn-version-{{sid}}:
  file.directory:
    - name: "{{ '/'.join(dest.split('/')[:-1]) }}"
    - makedirs: true
    - user: root
    - mode: 755
    - watch:
      - mc_proxy: mvn-pre-prefix-install
  archive.extracted:
    - name: "{{dest}}"
    - unless: "{{dest}}/bin/mvn --version"
    - if_missing: "{{dest}}/bin/.mvn_{{version}}"
    - source: "{{url}}"
    - archive_format: tar
    {% if hash %}
    - source_hash: "{{hash}}"
    {% endif %}
    - watch_in:
      - mc_proxy: mvn-post-prefix-install
    - watch:
      - file: mvn-version-{{sid}}
  cmd.run:
    - name: |
            mv -vf {{dest}}/*{{version}}*/* "{{dest}}"
            rm -rf {{dest}}/*{{version}}*
    - onlyif: "test -e {{dest}}/*{{version}}*"
    - user: root
    - watch:
      - archive: mvn-version-{{sid}}
    - watch_in:
      - mc_proxy: mvn-post-prefix-install
{% if link %}
{% for exec in ['mvn', 'mvnDebug', 'mvnyjp'] %}
mvn-version-{{sid}}-link-{{exec}}:
  file.symlink:
    - name: "/usr/local/bin/{{exec}}"
    - target: "{{dest}}/bin/{{exec}}"
    - watch:
      - cmd: mvn-version-{{sid}}
    - watch_in:
      - mc_proxy: mvn-post-prefix-install
{% endfor %}
{% endif %}
{% endmacro %}

{% for version in settings.versions %}
{{ install(version, suf='auto') }}
{% endfor %}
