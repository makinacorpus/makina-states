{#
# locales managment
# see:
#   - makina-states/doc/ref/formulaes/localsettings/locales.rst
#}
{% set data = salt['mc_locales.settings']() %}
include:
  - makina-states.localsettings.locales.hooks

{% set locales = data.locales %}
{% set default_locale = data.locale %}
{% for locale in locales %}
{% set lid=locale.replace('@', '_').replace('.', '_').replace('-', '_')%}
{% set localeo = locale %}
{% set locale = locale.replace('-', '').replace('utf8', 'UTF-8').replace('UTF8', 'UTF-8') %}
gen-makina-locales-{{ lid }}:
  cmd.run:
    - name: export PATH="${PATH}:/usr/sbin:/sbin";locale-gen {{locale}}
    - onlyif: test -e /sbin/locale-gen || test -e /usr/sbin/locale-gen
    - unless: locale -a|sed -re "s/utf8/UTF-8/g"|grep -q {{ locale }}
    - watch_in:
      - cmd: update-makina-locale
      - mc_proxy: locales-post-conf
    - watch:
      - mc_proxy: locales-pre-conf
{% if localeo != locale %}
nondash-gen-makina-locales-{{ lid }}:
  cmd.run:
    - name:  export PATH="${PATH}:/usr/sbin:/sbin";locale-gen {{localeo}}
    - onlyif: test -e /sbin/locale-gen || test -e /usr/sbin/locale-gen
    - unless: locale -a|sed -re "s/utf8/UTF-8/g"|grep -q {{ locale }}
    - watch_in:
      - cmd: update-makina-locale
    - watch_in:
      - cmd: update-makina-locale
      - mc_proxy: locales-post-conf
    - watch:
      - mc_proxy: locales-pre-conf
{% endif %}
{%- endfor %}
update-makina-locale:
  cmd.run:
    - name: 'update-locale LANG="{{ default_locale }}"'
    - onlyif: which update-locale
    - unless: "grep 'LANG={{ default_locale }}' /etc/default/locale"
    - watch_in:
      - mc_proxy: locales-post-conf
    - watch:
      - mc_proxy: locales-pre-conf

etc-profile.d-0_lang.sh:
  file.managed:
    - source: ''
    - makedirs: true
    - mode: 755
    - watch_in:
      - mc_proxy: locales-post-conf
    - watch:
      - mc_proxy: locales-pre-conf
    - name: /etc/profile.d/0_lang.sh
    - contents: |
                export LANG="{{ default_locale }}"
                export LC_CTYPE="{{ default_locale }}"
                export LC_NUMERIC="{{ default_locale }}"
                export LC_TIME="{{ default_locale }}"
                export LC_COLLATE="{{ default_locale }}"
                export LC_MONETARY="{{ default_locale }}"
                export LC_MESSAGES="{{ default_locale }}"
                export LC_PAPER="{{ default_locale }}"
                export LC_NAME="{{ default_locale }}"
                export LC_ADDRESS="{{ default_locale }}"
                export LC_TELEPHONE="{{ default_locale }}"
                export LC_MEASUREMENT="{{ default_locale }}"
                export LC_IDENTIFICATION="{{ default_locale }}"
                LC_ALL=""
