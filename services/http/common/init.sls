{% set settings = salt['mc_www.settings']() %}
include:
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.apache.hooks
  - makina-states.services.php.hooks
www-socks-dir:
  file.directory:
    - name: {{settings.socket_directory}}
    - mode: 1777
    - makedirs: true
    - user: root
    - group: root
    - watch_in:
      - mc_proxy: makina-apache-pre-inst
      - mc_proxy: makina-php-pre-inst
      - mc_proxy: nginx-pre-install-hook
