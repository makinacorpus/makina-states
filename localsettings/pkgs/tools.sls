include:
  - makina-states.localsettings.pkgs.hooks
useful-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: 
      - ifenslave-2.6
      - iptraf
      - nmap
      - sipcalc
      - whois
      - irssi
      - ntfs-3g
      - ppp
      - pppconfig
      - pppoeconf
      - ufw
      - ethtool
      - traceroute
      - iftop
    - watch:
      - mc_proxy: before-pkg-install-proxy
    - watch_in:
      - mc_proxy: after-pkg-install-proxy
 
