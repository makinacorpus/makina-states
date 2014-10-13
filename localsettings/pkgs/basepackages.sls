{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/pkgs.rst
#}

{{ salt['mc_macros.register']('localsettings', 'pkgs.basepackages') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.pkgs.hooks

{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
before-ubuntu-pkg-install-proxy:
  mc_proxy.hook:
    - watch:
        - mc_proxy: before-pkg-install-proxy
        - mc_proxy: after-base-pkgmgr-config-proxy
    - watch_in:
      {% if grains['os'] == 'Ubuntu' %}
      - pkg: ubuntu-pkgs
      {% endif %}
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs

after-ubuntu-pkg-install-proxy:
  mc_proxy.hook:
    - watch_in:
        - mc_proxy: after-pkg-install-proxy
    - watch:
      {% if grains['os'] == 'Ubuntu' %}
      - pkg: ubuntu-pkgs
      {% endif %}
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs
{% if grains['os'] == 'Ubuntu' -%}
ubuntu-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - apport
      - debian-archive-keyring
      - debian-keyring
      - language-pack-en
      - language-pack-fr
      - rsyslog
      - ca-certificates
      - ubuntu-cloudimage-keyring
      - ubuntu-cloud-keyring
      - ubuntu-extras-keyring
      - ubuntu-keyring
      - ubuntu-minimal
      - ubuntu-standard
{%- endif %}

sys-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - acpid
      - bridge-utils
      - acl
      - libacl1-dev
      - bash-completion
      - bzip2
      - cron
      - cronolog
      - dialog
      - findutils
      - htop
      - pv
      - links
      - locales
      - man-db
      - libopts25
      - manpages
      - manpages-fr
      - manpages-de
      {% if grains.get('osrelease', '') != '5.0.10' and (not grains.get('lsb_distrib_codename') in ['wheezy', 'sarge'])%}
      - jq
      {% endif %}
      - lsof
      - lvm2
      - lynx
      - mc
      - mlocate
      - gdisk
      - ncdu
      - psmisc
      - pwgen
      - python
      - python-dev
      - sudo
      - bsdtar
      - socat
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
      {%- endif %}
# too much consuming     
#      - atop
#      - vnstat

{% if 'devhost' in salt['mc_localsettings.registry']()['actives'] -%}
devhost-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - localepurge
{%- endif %}

dev-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - git
      - git-core
      {%- if grains['os_family'] == 'Debian' %}
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
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - wget
      - curl
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
      - wakeonlan
      - wget
      - whois

salt-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - python-apt
      - libgmp3-dev
{% endif %}
{% endif %}
