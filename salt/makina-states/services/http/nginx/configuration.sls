{% import "makina-states/_macros/h.jinja" as h with context %}
include:
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.nginx.services
  - makina-states.services.http.nginx.vhosts
{% set settings = salt['mc_nginx.settings']() %}
nginx-vhost-dirs:
  file.directory:
    - names:
      - {{settings.logdir}}
      - {{settings.basedir}}/conf.d
      - {{settings.basedir}}/sites-available
      - {{settings.basedir}}/sites-enabled
    - mode: 755
    - makedirs: true
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
makina-nginx-helman:
  cmd.run:
    - unless: test -e /etc/ssl/certs/nginxdhparam.pem
    - use_vt: true
    - name: |
            set -e
            cd /etc/ssl/certs
            openssl dhparam -out nginxdhparam.pem 2048
            chmod 644 nginxdhparam.pem
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
{% macro rmacro() %}
    - watch:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
{% endmacro %}
{{ h.deliver_config_files(
     settings.get('configs', {}),
     mode='644',
     after_macro=rmacro, prefix='nginx-')}}

nginxservice-systemd-reload-conf:
  cmd.run:
    - name: "systemctl daemon-reload"
    - watch:
      - file: nginx-/etc/systemd/system/overrides.d/nginx.conf
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
