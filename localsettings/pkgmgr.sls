{#-
# Manage apt mirrors:
# To override in pillars do:
# Goal is only to manage official mirrors, for
# thirdparty repositories, you may have better to write
# a file in /etc/apt/sources.list.d/foo.list or use
# the salt pkgrepo.installed state.
#
# To override settings:
#
# debian like (debian, ubuntu):
# makina-states.apt.ubuntu.comps: main (defaults: main restricted universe multiverse)
# makina-states.apt.debian.comps: main (defaults: main contrib non-free)
# makina-states.apt.use-backports: use back-ports
# makina-states.apt.settings:
#   mirrors:
#     - mirror: http://1
#       dists: wheezy-foo
#       comps: uber-non-free
#     - mirror: http://2
#       dists: wheezy-foo2
#       comps: uber-non-free2
#       no-src: True #(do not add a deb-src entry; false by default)
#   use-backports: true|false
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{- localsettings.register('pkgmgr') }}
{%- set locs = localsettings.locations %}
{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
{%- set bp = salt['mc_utils.get']('makina-states.apt.use-backports', True) %}
{%- set ddist = localsettings.ddist %}
{%- set udist = localsettings.udist %}
{%- set dist = grains.get('lsb_distrib_codename', '') %}
{%- set debian_mirror = localsettings.debian_mirror %}
{%- set ubuntu_mirror = localsettings.ubuntu_mirror %}
{%- set dcomps = localsettings.dcomps %}
{%- set ucomps = localsettings.ucomps %}
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
apt-sources-list:
  file.managed:
    - name: {{ locs.conf_dir }}/apt/sources.list
    - source: salt://makina-states/files/etc/apt/sources.list
    - mode: 755
    - template: jinja
    - pkg_data: {{ pkg_data | yaml }}

apt-update-after:
  cmd.watch:
    - name: apt-get update
    - watch:
      - file: apt-sources-list
{% endif %}
# vim:set nofoldenable:
