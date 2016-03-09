{% import "makina-states/services/http/apache/configuration.sls" as apache with context %}
{% set locs = salt['mc_locations.settings']() %}
{% set apacheSettings = salt['mc_apache.settings']() %}
include:
  - makina-states.services.php.hooks
  - makina-states.services.http.apache.hooks
  - makina-states.services.http.apache

makina-fcgid-apache-module_connect_fcgid_mod_fcgid_module_conf:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ locs.conf_dir }}/apache2/mods-available/fcgid.conf
    - source: salt://makina-states/files/etc/apache2/mods-available/fcgid.conf
    - template: 'jinja'
    - defaults:
        enabled: {{ apacheSettings.fastcgi_enabled }}
        socket_directory:  '{{apacheSettings.fastcgi_socket_directory}}'
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart

makina-fcgid-apache-module_connect_fcgid_notproxyfcgi:
  mc_apache.exclude_modules:
    - modules:
      - proxy_fcgi
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_apache: makina-apache-main-conf

makina-fcgid-apache-module_connect_fcgid:
  mc_apache.include_modules:
    - modules:
      - fcgid
      - actions
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_apache: makina-apache-main-conf

