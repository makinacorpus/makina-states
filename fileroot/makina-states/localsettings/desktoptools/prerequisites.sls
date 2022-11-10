include:
  - makina-states.localsettings.pkgs.basepackages
  - makina-states.localsettings.desktoptools.hooks
{% if grains['os'] in ['Ubuntu'] %}
chrome-base:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: chrome ppa
    - name: deb http://dl.google.com/linux/chrome/deb/ stable main
    - dist: stable
    - file: /etc/apt/sources.list.d/chrome.list
    - key_url: https://dl-ssl.google.com/linux/linux_signing_key.pub
    - watch:
      - mc_proxy: ms-desktoptools-pkgm-pre
    - watch_in:
      - mc_proxy: ms-desktoptools-pkgm-post

desktop-pkgs:
  pkg.latest:
    - pkgs:
      # office
      - gimp
      - firefox
      - thunderbird
      - libreoffice
      - vlc
      - smplayer
      - google-chrome-unstable
      - pinentry
      - enigmail
      - burp
      - mumble
      - skype
      # dev/net
      - corkscrew
      - proxytunnel
      - kcachegrind
      - golang
      - aircrack-ng
    - watch:
      - mc_proxy: ms-desktoptools-pkg-pre
    - watch_in:
      - mc_proxy: ms-desktoptools-pkg-post
{% endif %}
