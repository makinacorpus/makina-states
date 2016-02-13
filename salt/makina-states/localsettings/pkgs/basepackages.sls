{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/pkgs.rst
#}

{{ salt['mc_macros.register']('localsettings', 'pkgs.basepackages') }}
{% set light = salt['mc_nodetypes.is_docker']() or salt['mc_nodetypes.is_devhost']() %}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.localsettings.pkgs.hooks
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

after-ubuntu-pkg-install-proxy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: before-pkg-install-proxy
      - mc_proxy: before-ubuntu-pkg-install-proxy
      {% if grains['os'] == 'Ubuntu' %}
      - pkg: ubuntu-pkgs
      {% endif %}
      - pkg: sys-pkgs
    - watch_in:
      - mc_proxy: after-pkg-install-proxy

{% if grains['os'] == 'Ubuntu' -%}
ubuntu-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - debian-archive-keyring
      - debian-keyring
      - ubuntu-cloudimage-keyring
      - ubuntu-cloud-keyring
      {% if grains ['osrelease'] < '15.04' %}
      - ubuntu-extras-keyring
      {% endif %}
      - ubuntu-keyring
      # light version of ubuntu-minimal
      # those are harmful packages in a generic container context
      # - whiptail
      # - udev
      # - makedev
      # - initramfs-tools
      # - kbd
      # - kmod
      # - ureadahead
      {% if not light %}
      - update-manager-core
      - mtr-tiny
      {% endif %}
      - adduser
      - apt
      - apt-utils
      - console-setup
      - ca-certificates
      - debconf
      - debconf-i18n
      - ifupdown
      - iputils-ping
      - locales
      - lsb-release
      - mawk
      - netbase
      - passwd
      - procps
      - python3
      - resolvconf
      - sudo
      - tzdata
      - vim-tiny
      # light version of ubuntu-standard
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
      - time
      - apt-transport-https
      - iputils-tracepath
      - uuid-runtime
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
      - vim
      {% if salt['mc_controllers.allow_lowlevel_states']() %}
      - lvm2
      - bridge-utils
      {% endif %}
      - acl
      - bzip2
      - cron
      - findutils
      - locales
      {% if not nojq %}- jq{% endif %}
      - lsof
      - mlocate
      - netcat-openbsd
      - psmisc
      - gnupg
      - virt-what
      - python
      - bsdtar
      - screen
      - python-dev
      - sudo
      - tzdata
      - unzip
      - zip
      {% if grains['os_family'] == 'Debian' -%}
      - python-software-properties
      - debconf-utils
      - at
      {%- endif %}
      {% if salt['mc_nodetypes.is_devhost']() %}- localepurge{%- endif %}
      - git
      - git-core
      {# salt-pkgs #}
      - python-apt
      - libgmp3-dev
      {# net-pkgs #}
      - vlan
      - wget
      - curl
      {% if grains.get('osrelease', '') >= '13.10' %}
      - iproute2
      {% endif %}
      - rsync
      - openssh-client
      - socat
      - telnet
{% endif %}
