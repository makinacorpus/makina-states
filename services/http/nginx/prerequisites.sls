include:
  - makina-states.services.http.nginx.hooks

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
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/haproxy.list
    - keyid: 207A7A4E
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: nginx-pre-install-hook

makina-nginx-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ salt['mc_nginx.settings']().package }}
    - watch:
      - mc_proxy: nginx-pre-install-hook
      - pkgrepo: nginx-base
    - watch_in:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: nginx-pre-hardrestart-hook
      - mc_proxy: nginx-pre-restart-hook

