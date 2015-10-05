{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/pkgs.rst
#}

{{ salt['mc_macros.register']('localsettings', 'pkgs.basepackages') }}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.pkgs.hooks
  {% if not salt['mc_nodetypes.is_container']() %}
  - makina-states.localsettings.pkgs.tools
  {% endif %}

{% set pkgs = salt['mc_pkgs.settings']() %}

{%- if grains['os'] in ['Ubuntu', 'Debian'] %}
before-ubuntu-pkg-install-proxy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: before-pkg-install-proxy
    - watch_in:
      - mc_proxy: after-pkg-install-proxy
      {% if grains['os'] == 'Ubuntu' %}
      - pkg: ubuntu-pkgs
      {% endif %}
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs

after-ubuntu-pkg-install-proxy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: before-pkg-install-proxy
      - mc_proxy: before-ubuntu-pkg-install-proxy
      {% if grains['os'] == 'Ubuntu' %}
      - pkg: ubuntu-pkgs
      {% endif %}
      - pkg: sys-pkgs
      - pkg: dev-pkgs
      - pkg: net-pkgs
      - pkg: salt-pkgs
    - watch_in:
      - mc_proxy: after-pkg-install-proxy

{% if grains['os'] == 'Ubuntu' -%}
ubuntu-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - debian-archive-keyring
      - debian-keyring
      - ca-certificates
      - ubuntu-cloudimage-keyring
      - ubuntu-cloud-keyring
      {% if grains ['osrelease'] < '15.04' %}
      - ubuntu-extras-keyring
      {% endif %}
      - ubuntu-keyring
      # light version of ubuntu-minimal
      {% if not salt['mc_nodetypes.is_container']() %}
      - ubuntu-minimal
      {% else %}
      # those are harmful packages in a generic container context
      # - whiptail
      # - udev
      # - makedev
      # - initramfs-tools
      # - kbd
      # - kmod
      # - ureadahead
      {% if not salt['mc_nodetypes.is_docker']() %}
      - update-manager-core
      - mtr-tiny
      {% endif %}
      - adduser
      - apt
      - apt-utils
      - console-setup
      - debconf
      - debconf-i18n
      - ifupdown
      {% if grains.get('osrelease', '') >= '13.10' %}
      - iproute2
      {% endif %}
      - iputils-ping
      - locales
      - lsb-release
      - mawk
      - net-tools
      - netbase
      - netcat-openbsd
      - ntpdate
      - passwd
      - procps
      - python3
      - resolvconf
      - rsyslog
      - sudo
      - tzdata
      - vim-tiny
      {% endif %}
      # light version of ubuntu-standard
      {% if not salt['mc_nodetypes.is_container']() %}
      - ubuntu-standard
      {% else %}
      # those are harmful packages in a generic container context
      #- command-not-found
      #- friendly-recovery
      #- dmidecode
      #- pciutils
      #- usbutils
      #- apparmor
      #- irqbalance
      #- plymouth
      #- plymouth-theme-ubuntu-text
      - dmidecode
      - busybox-static
      - cpio
      - dosfstools
      - ed
      - file
      - ftp
      - iptables
      - language-selector-common
      - logrotate
      - mime-support
      {% if grains.get('osrelease', '') >= '15.04' %}
      - systemd-sysv
      {% endif %}
      - time
      - apt-transport-https
      - iputils-tracepath
      - uuid-runtime
      {% endif %}
{%- endif %}
{% if grains.get('osrelease', '') != '5.0.10' and (not grains.get('lsb_distrib_codename') in ['wheezy', 'sarge'])%}
{% set nojq = True%}
{% endif %}
{% if (grains.get('osrelease', '') <= '13.10' and grains['os'] in ['ubuntu']) %}
{% set nojq = True%}
{%endif%}
sys-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      {% if salt['mc_controllers.mastersalt_mode']() %}
      - lvm2
      - pv
      - bridge-utils
      {% endif %}
      - htop
      - acl
      - libacl1-dev
      - bash-completion
      - bzip2
      - cron
      - cronolog
      - dialog
      - findutils
      - locales
      - man-db
      - libopts25
      - manpages
      {% if not nojq %}
      - jq
      {% endif %}
      - lsof
      - mlocate
      - psmisc
      - debootstrap
      - gnupg
      - pwgen
      - virt-what
      - python
      - python-dev
      - sudo
      - bsdtar
      - socat
      - screen
      - tzdata
      - tree
      - unzip
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

net-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - wget
      - curl
      - dnsutils
      - net-tools
      - rsync
      - telnet
      - tcpdump
      {% if salt['mc_controllers.mastersalt_mode']() %}
      - openssh-client
      - ntp
      - vlan
      {% endif %}

salt-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - python-apt
      - libgmp3-dev
{% endif %}
