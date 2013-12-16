#
# Manage packages to install by default
#

include:
  - makina-states.localsettings.pkgmgr

{% if grains['os'] in ['Ubuntu', 'Debian'] %}
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

{% if grains['os'] == 'Ubuntu' -%}
ubuntu-pkgs:
  pkg.installed:
    - pkgs:
      - language-pack-en
      - language-pack-fr
      - ubuntu-minimal
      - ubuntu-standard
      - apport
      - rsyslog
{% endif %}

sys-pkgs:
  pkg.installed:
    - pkgs:
      - acpid
      - atop
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
      {% if grains['os_family'] == 'Debian' -%}
      - python-software-properties
      - debconf-utils
      - dstat
      {% endif %}


{% if grains.get('makina.nodetype.devhost', False) %}
devhost-pkgs:
  pkg.installed:
    - pkgs:
      - localepurge
{% endif %}

dev-pkgs:
  pkg.installed:
    - pkgs:
      - git
      - git-core
      {% if grains['os_family'] == 'Debian' -%}
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
      {% endif %}

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
{% endif %}
