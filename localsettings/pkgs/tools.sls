include:
  - makina-states.localsettings.pkgs.hooks

useful-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - ifenslave-2.6
      - iptraf
      - dialog
      - nmap
      - sipcalc
      - whois
      - irssi
      - ntfs-3g
      - ppp
      - tmux
      - lynx
      - acpid
      - smartmontools
      - ncdu
      - links
      - xfsprogs
      - mc
      - gdisk
      - manpages-de
      - pppconfig
      - pppoeconf
      - ufw
      - ethtool
      - traceroute
      - iftop
      - wakeonlan
      - openssh-server
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
      - zerofree
      - strace
      - nano
      - vim
      - language-pack-en
      - language-pack-fr
      - pv
      - htop
      - man-db
      - manpages
      - manpages-fr
      - debootstrap
      - pwgen
      - tree
      {# net-pkgs #}
      - dnsutils
      - net-tools
      - tcpdump
    - watch:
      - mc_proxy: before-pkg-install-proxy
    - watch_in:
      - mc_proxy: after-pkg-install-proxy
