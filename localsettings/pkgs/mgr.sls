{% import "makina-states/_macros/h.jinja" as h with context %}
{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/pkgmgr.rst
#}

include:
  - makina-states.localsettings.pkgs.hooks
{{ salt['mc_macros.register']('localsettings', 'pkgs.mgr') }}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = pkgssettings %}
{%- set locs = salt['mc_locations.settings']() %}
{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
apt-sources-list:
  file.managed:
    - watch:
      - mc_proxy: before-pkgmgr-config-proxy
    - watch_in:
      - mc_proxy: after-base-pkgmgr-config-proxy
    - name: {{ locs.conf_dir }}/apt/sources.list
    - source: salt://makina-states/files/etc/apt/sources.list
    - mode: 755
    - template: jinja

{% macro rmacro() %}
    - watch:
      - mc_proxy: before-pkgmgr-config-proxy
    - watch_in:
      - mc_proxy: after-base-pkgmgr-config-proxy
{% endmacro %}
{{ h.deliver_config_files(
     data.get('extra_confs', {}), after_macro=rmacro, prefix='localsettings-pkgmgr-')}}

{% if grains['os'] in ['Debian'] %}
{% if pkgssettings.ddist not in ['sid'] and grains.get('osrelease', '1')[0] > '5' %}
apt-sources-pref-sid:
  file.managed:
    - watch:
      - mc_proxy: before-pkgmgr-config-proxy
    - watch_in:
      - mc_proxy: after-base-pkgmgr-config-proxy
    - name: /etc/apt/preferences.d/sid.pref
    - source: salt://makina-states/files/etc/apt/preferences.d/sid.pref
    - mode: 755
    - template: jinja
    - makedirs: true

apt-sources-list-sid:
  file.managed:
    - watch:
      - mc_proxy: before-pkgmgr-config-proxy
    - watch_in:
      - mc_proxy: after-base-pkgmgr-config-proxy
    - name: {{ locs.conf_dir }}/apt/sources.list.d/sid.list
    - mode: 755
    - template: jinja
    - makedirs: true
    - contents: deb {{pkgssettings.data['debian_mirror']}} sid main contrib non-free
{% endif %}
{% endif %}

apt-update-after:
  cmd.watch:
    - name: apt-get update
    - watch:
      - mc_proxy: after-base-pkgmgr-config-proxy
    - watch_in:
      - mc_proxy: after-pkgmgr-config-proxy
{% endif %}
{% endif %}
# vim:set nofoldenable:
