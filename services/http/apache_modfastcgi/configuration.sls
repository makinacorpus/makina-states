{% import "makina-states/services/http/apache/configuration.sls" as apache with context %}
{% set locs = salt['mc_locations.settings']() %}
{% set phpSettings = salt['mc_php.settings']() %}
{% set apacheSettings = salt['mc_apache.settings']() %}

include:
  - makina-states.services.php.hooks
  - makina-states.services.http.apache.hooks
  - makina-states.services.http.apache

makina-fastcgi-apache-module_connect_fastcgi_mod_fastcgi_module_conf:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ locs.conf_dir }}/apache2/mods-available/fastcgi.conf
    - source: salt://makina-states/files/etc/apache2/mods-available/fastcgi.conf
    - template: 'jinja'
    - defaults:
        enabled: {{ apacheSettings.fastcgi_enabled }}
        socket_directory:  '{{apacheSettings.fastcgi_socket_directory}}'
        extra: |
               {{salt['mc_utils.json_dump'](apacheSettings.fastcgi_params)}}
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart

makina-fastcgi-apache-module_connect_fastcgi_notproxyfcgi:
  mc_apache.exclude_module:
    - modules:
      - proxy_fcgi
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_apache: makina-apache-main-conf

makina-fastcgi-apache-module_connect_fastcgi:
  mc_apache.include_module:
    - modules:
      - fastcgi
      - actions
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_apache: makina-apache-main-conf

