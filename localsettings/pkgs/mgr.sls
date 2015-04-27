{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/pkgmgr.rst
#}

include:
  - makina-states.localsettings.pkgs.hooks
{{ salt['mc_macros.register']('localsettings', 'pkgs.mgr') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
apt-sources-list:
  file.managed:
    - watch_in:
      - mc_proxy: before-pkgmgr-config-proxy
    - name: {{ locs.conf_dir }}/apt/sources.list
    - source: salt://makina-states/files/etc/apt/sources.list
    - mode: 755
    - template: jinja

{% if grains['os'] in ['Debian'] %}
{% if pkgssettings.ddist not in ['sid'] and grains.get('osrelease', '1')[0] > '5' %}
apt-sources-pref-sid:
  file.managed:
    - watch_in:
      - service: apt-update-after
    - name: /etc/apt/preferences.d/sid.pref
    - source: salt://makina-states/files/etc/apt/preferences.d/sid.pref
    - mode: 755
    - template: jinja
    - makedirs: true

apt-sources-list-sid:
  file.managed:
    - watch_in:
      - service: apt-update-after
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
    - watch_in:
      - mc_proxy: after-base-pkgmgr-config-proxy
{% endif %}
{% endif %}
# vim:set nofoldenable:
