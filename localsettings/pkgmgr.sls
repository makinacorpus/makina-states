{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/pkgmgr.rst
#}

{{ salt['mc_macros.register']('localsettings', 'pkgmgr') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
{%- set bp = salt['mc_utils.get']('makina-states.apt.use-backports', True) %}
{%- set ddist = pkgssettings.ddist %}
{%- set udist = pkgssettings.udist %}
{%- set dist = grains.get('lsb_distrib_codename', '') %}
{%- set debian_mirror = pkgssettings.debian_mirror %}
{%- set ubuntu_mirror = pkgssettings.ubuntu_mirror %}
{%- set dcomps = pkgssettings.dcomps %}
{%- set ucomps = pkgssettings.ucomps %}

{% if pkgssettings.ddist not in ['sid'] and grains.get('osrelease', '1')[0] <='5' %}
{% set upt = 'volatile' %}
{% else %}
{% set upt = 'updates' %}
{% endif %}
{%- set pkg_data = salt['grains.filter_by']({
  'default': {'mirrors': []},
  'Debian': {'use-backports': True, 'mirrors': [
    {'mirror': debian_mirror,
    'dists': [
      {'name': ddist, 'comps': dcomps},
      {'name': ddist+'-updates', 'comps': dcomps}]},
    {'mirror': 'http://security.debian.org/',
    'dists': [
    {'name': ddist+'/updates', 'comps': dcomps}]},
  ]},
  'Ubuntu': {'mirrors' :[
    {'mirror': ubuntu_mirror,
     'dists': [
      {'name': udist, 'comps': ucomps,},
      {'name': udist+'-updates', 'comps': ucomps,},
      {'name': udist+'-security', 'comps': ucomps,}]},
    {'mirror': 'http://archive.canonical.com/ubuntu',
     'dists': [{'name': udist, 'comps': 'partner'}]},
    {'mirror': 'http://extras.ubuntu.com/ubuntu',
     'dists': [{'name': udist, 'comps': 'main'}]},
    ]} }, grain='os') %}


{%- set pillar_data = salt['pillar.get']('makina-states.apt.settings', {}) %}
{%- set pkg_data=salt['mc_utils.dictupdate'](pkg_data, pillar_data) %}
{%- if bp %}
{%- do pkg_data['mirrors'].extend(
  salt['grains.filter_by']({
    'Debian': [
    {'mirror': debian_mirror,
    'dists': [{'name': ddist+'-backports', 'comps': dcomps}]}],
    'Ubuntu': [
    {'mirror':  ubuntu_mirror,
    'dists': [{'name': udist+'-backports', 'comps': ucomps}]}
    ]}, grain='os'))  %}
{%- endif %}

{% if grains['os'] in ['Debian'] %}
{% if pkgssettings.ddist not in ['sid'] and grains.get('osrelease', '1')[0] <='5' %}
{% do pkg_data['mirrors'][0]['dists'].pop(1) %}
{% do pkg_data['mirrors'].pop(1) %}
{% do pkg_data['mirrors'].pop(1) %}
{%- do pkg_data['mirrors'].extend(
  salt['grains.filter_by']({
    'Debian': [
        {'mirror': 'http://archive.debian.org/debian-security',
        'dists': [{'name': ddist+'/updates', 'comps': dcomps}]},
        {'mirror': 'http://archive.debian.org/debian-volatile',
        'dists': [{'name': ddist+'/volatile', 'comps': dcomps}]},
        {'mirror': 'http://archive.debian.org/backports.org',
        'dists': [{'name': ddist+'-backports', 'comps': dcomps}]}
    ]}))  %}
{% endif%}
{% endif%}
apt-sources-list:
  file.managed:
    - name: {{ locs.conf_dir }}/apt/sources.list
    - source: salt://makina-states/files/etc/apt/sources.list
    - mode: 755
    - template: jinja
    - pkg_data: |
                {{ salt['mc_utils.json_dump'](pkg_data) }}

{% if grains['os'] in ['Debian'] %}
{% if pkgssettings.ddist not in ['sid'] and grains.get('osrelease', '1')[0] > '5' %}
apt-sources-pref-sid:
  file.managed:
    - watch_in:
      - service: apt-update-after
    - name: {{ locs.conf_dir }}/apt/preferences.d/sid.pref
    - mode: 755
    - template: jinja
    - makedirs: true
    - contents: |
                Package: *
                Pin: release a=stable
                Pin-Priority: 700

                Package: *
                Pin: release a=testing
                Pin-Priority: 650

                Package: *
                Pin: release a=unstable
                Pin-Priority: 600

apt-sources-list-sid:
  file.managed:
    - watch_in:
      - service: apt-update-after
    - name: {{ locs.conf_dir }}/apt/sources.list.d/sid.list
    - mode: 755
    - template: jinja
    - makedirs: true
    - contents: deb {{pkgssettings.debian_mirror}} sid main contrib non-free
{% endif %}
{% endif %}

apt-update-after:
  cmd.watch:
    - name: apt-get update
    - watch:
      - file: apt-sources-list
{% endif %}
{% endif %}
# vim:set nofoldenable:
