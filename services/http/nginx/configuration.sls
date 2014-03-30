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

{% set data = {
  'settings': settings
} %}
{% set sdata = data| yaml %}
{% set sdata.replace('\n', ' ') %}
{% for f in [
    settings['basedir'] + 'fastcgi_params',
    settings['basedir'] + 'koi-utf',
    settings['basedir'] + 'koi-win',
    settings['basedir'] + 'mime.types',
    settings['basedir'] + 'naxsi.rules',
    settings['basedir'] + 'naxsi_core.rules',
    settings['basedir'] + 'nginx.conf',
    settings['basedir'] + 'proxy_params',
    settings['basedir'] + 'scgi_params',
    settings['basedir'] + 'uwsgi_params',
    settings['basedir'] + 'win-utf',
    settings['basedir'] + 'sites-available/default.conf',
    '/etc/default/nginx',
] %}
makina-nginx-minimal-{{f}}:
  file.managed:
    - watch:
      - pkg: makina-nginx-pkgs
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - template: jinja
    - defaults:
      - sdata: "{{sdata}}"
    - user: root
    - group: root
    - makedirs: true
    - mode: 644
    - template: jinja
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
{% endfor %}
