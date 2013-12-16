#
# Manage system locales
#
# You can override default locales by adding them in pillar ths way:
# makina-locale: fr_FR.utf8
# makina-locales:
#   - fr_FR.utf8
#

include:
  - makina-states.localsettings.shell

locales-pkg:
  pkg.installed:
    - pkgs:
      - locales

{% set default_locale = 'fr_FR.UTF-8' %}
{% set default_locales = [
  'de_DE.UTF-8',
  'fr_BE.UTF-8',
  'fr_FR.UTF-8',
  ] %}

{% set locales = salt['config.get']('makina-locales', default_locales) %}
{% set default_locale = salt['config.get']('makina-locale', default_locale) %}

{% for locale in locales %}
{% set lid=locale.replace('@', '_').replace('.', '_').replace('-', '_') %}
gen-makina-locales-{{lid}}:
  cmd.run:
    - name: /usr/sbin/locale-gen {{locale}}
    - onlyif: test -e /usr/sbin/locale-gen
    - unless: locale -a|sed -re "s/utf8/UTF-8/g"|grep -q {{locale}}
    - require_in:
      - cmd: update-makina-locale

{% endfor %}
update-makina-locale:
  cmd.run:
    - name: update-locale LANG="{{default_locale}}"
    - onlyif: which update-locale
    - unless: grep 'LANG={{default_locale}}' /etc/default/locale

/etc/profile.d/0_lang.sh:
  file.managed:
    - contents: |
                export LANG="{{default_locale}}"
    - requires:
      - file: /etc/profile.d


