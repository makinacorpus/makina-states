{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_icinga_web.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/php/init.sls" as php with context %}

include:
  - makina-states.services.php.phpfpm_with_nginx
  - makina-states.services.http.nginx
  - makina-states.services.monitoring.icinga_web.hooks

# create a virtualhost in nginx
{{ nginx.virtualhost(**data.nginx)}}

# add a pool php-fpm
{{php.fpm_pool(domain=data.nginx.domain, **data.phpfpm)}}

# install php5-pgsql
icinga_web-php5-deps:
  pkg.{{pkgssettings['installmode']}}:
    - watch_in:
      - mc_proxy: icinga_web-pre-install
    - pkgs:
      {% for package in data.phpfpm.extensions_packages %}
      - {{package}}
      {% endfor %}

# configure content of doc_root
icinga_web-www-dir:
  file.directory:
    - name: {{data.nginx.doc_root}}
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: icinga_web-pre-install

icinga_web-www-dir-link-docroot:
  file.symlink:
    - name: {{data.nginx.doc_root}}/{{data.nginx.icinga_web.web_directory}}
    - target: /usr/share/icinga-web/pub
    - watch:
      - file: icinga_web-www-dir
    - watch_in:
      - mc_proxy: icinga_web-pre-install

icinga_web-www-dir-pub:
  file.directory:
    - name: {{data.nginx.doc_root}}/pub
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - file: icinga_web-www-dir-link-docroot
    - watch_in:
      - mc_proxy: icinga_web-pre-install

icinga-web-www-dir-js:
  file.symlink:
    - name: {{data.nginx.doc_root}}/pub/js
    - target: /usr/share/icinga-web/lib
    - watch:
      - file: icinga_web-www-dir-pub
    - watch_in:
      - mc_proxy: icinga_web-pre-install

