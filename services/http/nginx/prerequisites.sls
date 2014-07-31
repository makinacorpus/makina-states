include:
  - makina-states.services.http.nginx.hooks

{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% if grains['os_family'] in ['Debian'] %}
{% set dist = pkgssettings.udist %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% set dist = pkgssettings.ubuntu_lts %}
{% endif %}
nginx-base:
  pkgrepo.managed:
    - humanname: nginx ppa
    - name: deb http://ppa.launchpad.net/makinacorpus/nginx/ubuntu {{dist}} main

    - dist: {{dist}}
    - file: /etc/apt/sources.list.d/nginx.list
    - keyid: 207A7A4E
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: nginx-pre-install-hook

# clean typo in old confs
nginx-clean:
  cmd.run:
    - name: sed -i -e "/nginx/d" /etc/apt/sources.list.d/haproxy.list
    - onlyif: test -e /etc/apt/sources.list.d/haproxy.list && grep -q nginx /etc/apt/sources.list.d/haproxy.list
    - watch:
      - mc_proxy: nginx-pre-install-hook
      - pkgrepo: nginx-base
    - watch_in:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: nginx-pre-hardrestart-hook
      - mc_proxy: nginx-pre-restart-hook

makina-nginx-pkgs:
  pkg.latest:
    - pkgs:
      - {{ salt['mc_nginx.settings']().package }}
    - watch:
      - mc_proxy: nginx-pre-install-hook
      - pkgrepo: nginx-base
    - watch_in:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: nginx-pre-hardrestart-hook
      - mc_proxy: nginx-pre-restart-hook

