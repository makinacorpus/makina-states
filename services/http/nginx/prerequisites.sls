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
  pkgrepo.managed:
    - humanname: nginx ppa
    - name: deb http://ppa.launchpad.net/makinacorpus/nginx/ubuntu {{pkgssettings.ppa_dist}} main
    - dist: {{pkgssettings.ppa_dist}}
    - file: /etc/apt/sources.list.d/nginx.list
    - keyid: 207A7A4E
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: nginx-pre-install-hook
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

nginxservice-systemd-override-dir:
  file.directory:
    - makedirs: true
    - user: root
    - group: root
    - mode: 775
    - names:
      - /etc/systemd/system/nginx.service.d
    - watch_in:
      - mc_proxy: nginx-post-install-hook

nginxservice-systemd-config-override:
  file.managed:
    - user: root
    - group: root
    - makedirs: true
    - mode: 664
    - name: /etc/systemd/system/nginx.service.d/override.conf
    - source: salt://makina-states/files/etc/systemd/system/overrides.d/nginx.conf
    - template: 'jinja'
    - require:
      - pkg: makina-nginx-pkgs
      - file: nginxservice-systemd-override-dir
    - watch_in:
      - mc_proxy: nginx-post-install-hook

nginxservice-systemd-reload-conf:
  cmd.run:
    - name: "systemctl daemon-reload"
    - onchanges:
      - file: nginxservice-systemd-config-override
