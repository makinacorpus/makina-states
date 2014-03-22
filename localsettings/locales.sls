{#-
# locales managment
# see:
#   - makina-states/doc/ref/formulaes/localsettings/locales.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'locales') }}
{%- set locs = salt['mc_localsettings']()['locations'] %}
include:
  - makina-states.localsettings.shell

{%- if grains['os_family'] not in ['Debian'] %}FAIL HARD{% endif %}
{%- if grains['os_family'] in ['Debian'] %}
locales-pkg:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - locales

{%- set locales = localsettings.locales %}
{%- set default_locale = localsettings.default_locale %}
{%- for locale in locales %}
{%- set lid=locale.replace('@', '_').replace('.', '_').replace('-', '_') %}
gen-makina-locales-{{ lid }}:
  cmd.run:
    - name: {{ locs.sbin_dir }}/locale-gen {{ locale }}
    - onlyif: test -e {{ locs.sbin_dir }}/locale-gen
    - unless: locale -a|sed -re "s/utf8/UTF-8/g"|grep -q {{ locale }}
    - require_in:
      - cmd: update-makina-locale

{%- endfor %}
update-makina-locale:
  cmd.run:
    - name: 'update-locale LANG="{{ default_locale }}"'
    - onlyif: which update-locale
    - unless: "grep 'LANG={{ default_locale }}' {{ locs.conf_dir }}/default/locale"

etc-profile.d-0_lang.sh:
  file.managed:
    - requires:
      - file: etc-profile.d
    - name: {{ locs.conf_dir }}/profile.d/0_lang.sh
    - contents: |
                export LANG="{{ default_locale }}"
{% endif %}
