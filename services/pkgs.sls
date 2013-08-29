sys-pkgs:
  pkg.installed:
    - names:
      - screen
      - bzip2
      - vim
      - atop
      - bash-completion
      {% if grains['os_family'] == 'Debian' -%}
      - debconf-utils
      - dstat
      {% endif %}
      - findutils
      - htop
      - links
      - tree
      - lsof
      - lynx
      - mc
      - mlocate
      - psmisc
      - pwgen
      - smartmontools
      - unzip
      - zip

dev-pkgs:
  pkg.installed:
    - names:
      - git
      - git-core
      - python
      - python-dev
      {% if grains['os_family'] == 'Debian' -%}
      - build-essential
      - m4
      - libtool
      - pkg-config
      - autoconf
      - gettext
      - groff
      - man-db
      - automake
      - libsigc++-2.0-dev
      - tcl8.5
      {% endif %}

net-packages:
  pkg:
    - installed
    - names:
      - dnsutils
      - ethtool
      - ifenslave-2.6
      - iftop
      - iptraf
      - nmap
      - ntp
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
