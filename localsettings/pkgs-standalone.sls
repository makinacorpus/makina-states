{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/pkgs.rst
#}

{% macro do(full=True) %}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'pkgs') }}
{%- set locs = localsettings.locations %}

{% if full %}
include:
  - makina-states.localsettings.pkgmgr
  - makina-states.localsettings.pkgs-hooks
{% endif %}

{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
before-ubuntu-pkg-install-proxy:
  mc_proxy.hook:
    {% if full %}
    - watch:
        - file: apt-sources-list
        - mc_proxy: before-pkg-install-proxy
        - cmd: apt-update-after
    {% endif %}
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
  pkg.{{localsettings.installmode}}:
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
  pkg.{{localsettings.installmode}}:
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
      - jq
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
      - bsdtar
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

{% if 'devhost' in localsettings.registry['actives'] -%}
devhost-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - localepurge
{%- endif %}

dev-pkgs:
  pkg.{{localsettings.installmode}}:
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
  pkg.{{localsettings.installmode}}:
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
      - vnstat
      - wakeonlan
      - wget
      - whois

salt-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - python-apt
      - libgmp3-dev
{% endif %}
{% endmacro %}
{{ do(full=False)}}
