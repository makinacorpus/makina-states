{#-
# Manage packages to install by default
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{- localsettings.register('pkgs') }}
{%- set locs = localsettings.locations %}
include:
  - {{ localsettings.statesPref }}pkgmgr

{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
before-pkg-install-proxy:
  cmd.run:
    - unless: /bin/true
    - require:
      - file: apt-sources-list
      - cmd: apt-update-after
    - require_in:
      {% if grains['os'] == 'Ubuntu' %}
      - pkg: ubuntu-pkgs
      {% endif %}
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs

{%- if grains['os'] == 'Ubuntu' -%}
ubuntu-pkgs:
  pkg.installed:
    - pkgs:
      - apport
      - debian-archive-keyring
      - debian-keyring
      - language-pack-en
      - language-pack-fr
      - rsyslog
      - ubuntu-cloudimage-keyring
      - ubuntu-cloud-keyring
      - ubuntu-extras-keyring
      - ubuntu-keyring
      - ubuntu-minimal
      - ubuntu-standard
{%- endif %}

sys-pkgs:
  pkg.installed:
    - pkgs:
      - acpid
      - atop
      - acl
      - libacl1-dev
      - bash-completion
      - bzip2
      - cron
      - cronolog
      - dialog
      - findutils
      - htop
      - links
      - locales
      - man-db
      - libopts25
      - manpages
      - manpages-fr
      - manpages-de
      - lsof
      - lvm2
      - lynx
      - mc
      - mlocate
      - ncdu
      - psmisc
      - pwgen
      - python
      - python-dev
      - sudo
      - screen
      - smartmontools
      - tmux
      - screen
      - tzdata
      - tree
      - unzip
      - vim
      - xfsprogs
      - zerofree
      - zip
      {%- if grains['os_family'] == 'Debian' -%}
      - python-software-properties
      - debconf-utils
      - dstat
      {%- endif %}

{%- if grains.get('makina-states.nodetype.devhost', False) %}
devhost-pkgs:
  pkg.installed:
    - pkgs:
      - localepurge
{%- endif %}

dev-pkgs:
  pkg.installed:
    - pkgs:
      - git
      - git-core
      {%- if grains['os_family'] == 'Debian' -%}
      - build-essential
      - m4
      - libtool
      - pkg-config
      - autoconf
      - gettext
      - groff
      - automake
      - libsigc++-2.0-dev
      - tcl8.5
      {%- endif %}

net-pkgs:
  pkg:
    - installed
    - pkgs:
      - dnsutils
      - ethtool
      - ifenslave-2.6
      - iftop
      - iptraf
      - net-tools
      - nmap
      - ntp
      - openssh-server
      - rsync
      - sipcalc
      - tcpdump
      - telnet
      - traceroute
      - vlan
      - vnstat
      - wakeonlan
      - wget
      - whois

salt-pkgs:
  pkg.installed:
    - pkgs:
      - python-apt
      - libgmp3-dev
{% endif %}
