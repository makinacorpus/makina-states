#
# Manage apt mirrors:
# To override in pillars do:
# Goal is only to manage official mirrors, for
# thirdparty repositories, you may have better to write
# a file in /etc/apt/sources.list.d/foo.list or use
# the salt pkgrepo.installed state.
#
# To override settings:

# debian like (debian, ubuntu):
# makina.apt.ubuntu.comps: main (defaults: main restricted universe multiverse)
# makina.apt.debian.comps: main (defaults: main contrib non-free)
# makina.apt.use-backports: use back-ports
# makina.apt.settings:
#   mirrors:
#     - mirror: http://1
#       dists: wheezy-foo
#       comps: uber-non-free
#     - mirror: http://2
#       dists: wheezy-foo2
#       comps: uber-non-free2
#       no-src: True #(do not add a deb-src entry; false by default)
#   use-backports: true|false

{% if grains['os'] in ['Ubuntu', 'Debian'] %}
{% set bp = salt['config.get']('makina.apt.use-backports', False) %}
{% set udist = salt['config.get']('lsb_distrib_codename', 'precise') %}
{% set ddist = salt['config.get']('lsb_distrib_codename', 'wheezy') %}
{% set ubuntu_mirror = salt['config.get']('makina.apt.ubuntu.mirror',
                                          'http://ftp.free.fr/mirrors/ftp.ubuntu.com/ubuntu') %}
{% set debian_mirror = salt['config.get']('makina.apt.ubuntu.mirror',
                                          'http://ftp.de.debian.org/debian') %}
{% set dcomps = salt['config.get']('makina.apt.debian.comps',
                                   'main contrib non-free' ) %}
{% set ucomps = salt['config.get']('makina.apt.ubuntu.comps',
                                   'main restricted universe multiverse') %}
{% set pkg_data = salt['grains.filter_by']({
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
    ]}}, grain='os') %}
{% set pillar_data = salt['pillar.get']('makina.apt.settings', {}) %}
{% set pkg_data=salt['mc_utils.dictupdate'](pkg_data, pillar_data) %}
{% if bp %}
{% set dummy = pkg_data['mirrors'].extend(
  salt['grains.filter_by']({
    'Debian': [
    {'mirror': 'http://ftp.de.debian.org/debian',
    'dists': [{'name': 'jessie'+'-backports', 'comps': dcomps}]}],
    'Ubuntu': [
    {'mirror': 'http://ftp.de.debian.org/debian',
    'dists': [{'name': ddist+'-backports', 'comps': ucomps}]}
    ]}, grain='os'))  %}
{% endif %}

apt-sources-list:
  file.managed:
    - name: /etc/apt/sources.list
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
