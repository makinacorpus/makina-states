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

{% set modes = {
  '/etc/init.d/nginx-naxsi-ui': 755,
  '/etc/init.d/nginx': 755,
} %}

{% set sdata =salt['mc_utils.json_dump'](settings)  %}
{% for f in [
    '/etc/logrotate.d/nginx',
] %}
makina-nginx-minimal-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - user: root
    - mode: 644
    - group: root
    - makedirs: true
    - mode: {{modes.get(f, 644)}}
    - template: jinja
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
{% endfor %}

{# disable naxsi
'/usr/share/nginx-naxsi-ui/naxsi-ui/nx_extract.py',
'/etc/init.d/nginx-naxsi-ui',
'/etc/default/nginx-naxsi-ui',
settings['basedir'] + '/naxsi.conf',
settings['basedir'] + '/naxsi-ui.conf',
#}
{% for f in [
    settings['basedir'] + '/drupal_cron_allowed_hosts.conf',
    settings['basedir'] + '/fastcgi_fpm_drupal.conf',
    settings['basedir'] + '/fastcgi_fpm_drupal_params.conf',
    settings['basedir'] + '/fastcgi_fpm_drupal_private_files.conf',
    settings['basedir'] + '/fastcgi_microcache_zone.conf',
    settings['basedir'] + '/fastcgi_params',
    settings['basedir'] + '/fastcgi_params_common',
    settings['basedir'] + '/koi-utf',
    settings['basedir'] + '/koi-win',
    settings['basedir'] + '/map_cache.conf',
    settings['basedir'] + '/microcache_fcgi.conf',
    settings['basedir'] + '/mime.types',
    settings['basedir'] + '/naxsi_core.rules',
    settings['basedir'] + '/nginx.conf',
    settings['basedir'] + '/php_fpm_status_vhost.conf',
    settings['basedir'] + '/php_fpm_status_allowed_hosts.conf',
    settings['basedir'] + '/proxy_params',
    settings['basedir'] + '/scgi_params',
    settings['basedir'] + '/status_allowed_hosts.conf',
    settings['basedir'] + '/status_vhost.conf',
    settings['basedir'] + '/uwsgi_params',
    settings['basedir'] + '/win-utf',
    '/etc/default/nginx',
    '/etc/init.d/nginx',
] %}
makina-nginx-minimal-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - user: root
    - group: root
    - makedirs: true
    - mode: {{modes.get(f, 644)}}
    - template: jinja
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
{% endfor %}

