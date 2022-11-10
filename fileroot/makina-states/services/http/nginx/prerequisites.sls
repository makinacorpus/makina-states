include:
  - makina-states.services.http.nginx.hooks

{% set pkgssettings = salt['mc_pkgs.settings']() %}
nginx-clean:
  cmd.run:
    - name: sed -i -e "/nginx/d" /etc/apt/sources.list.d/nginx.list && echo "changed=false"
    - stateful: true
    - onlyif: |
              if test -e /etc/apt/sources.list.d/nginx.list;then
                grep -q nginx /etc/apt/sources.list.d/nginx.list;exit ${?};
              fi
              exit 1
    - watch:
      - mc_proxy: nginx-pre-install-hook
    - watch_in:
      - pkgrepo: nginx-base
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: nginx-pre-hardrestart-hook
      - mc_proxy: nginx-pre-restart-hook
{# clean typo in old confs #}
nginx-base:
  file.managed:
    - name: "/etc/apt/preferences.d/99_nginx.pref"
    - source: "salt://makina-states/files/etc/apt/preferences.d/99_nginx.pref"
    - mode: 644
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: nginx-pre-install-hook
    - watch_in:
      - pkgrepo: nginx-base
  cmd.run:
    - name: sed -re "/makinacorpus/d" -i /etc/apt/sources.list.d/nginx.list
    - onlyif: grep -q makinacorpus /etc/apt/sources.list.d/nginx.list
    - watch:
      - mc_proxy: nginx-pre-install-hook
    - watch_in:
      - pkgrepo: nginx-base
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: nginx ppa
    - name: deb http://ppa.launchpad.net/corpusops/nginx/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: /etc/apt/sources.list.d/nginx.list
    - keyid: 4420973F
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: nginx-pre-install-hook
    - watch_in:
      - pkg: makina-nginx-pkgs
makina-nginx-pkgs:
  pkg.latest:
    - pkgs:
      - {{ salt['mc_nginx.settings']().package }}
    - watch:
      - mc_proxy: nginx-pre-install-hook
    - watch_in:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: nginx-pre-hardrestart-hook
      - mc_proxy: nginx-pre-restart-hook
