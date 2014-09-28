{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_nagvis.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/php/init.sls" as php with context %}

include:
  - makina-states.services.php.phpfpm_with_nginx
  - makina-states.services.http.nginx
  - makina-states.services.monitoring.nagvis.hooks

# create a virtualhost in nginx
{{ nginx.virtualhost(**data.nginx)}}

# add a pool php-fpm
{{php.fpm_pool(domain=data.nginx.domain, **data.phpfpm)}}

# install php5 dependancies
nagvis-php5-deps:
  pkg.{{pkgssettings['installmode']}}:
    - watch_in:
      - mc_proxy: nagvis-pre-install
    - pkgs:
      {% for package in data.phpfpm.extensions_packages %}
      - {{package}}
      {% endfor %}

# symlink
nagvis-www-dir:
  file.directory:
    - name: {{data.nginx.doc_root}}
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch_in:
      - mc_proxy: nagvis-pre-install


nagvis-www-dir-link-docroot:
  file.symlink:
    - name: {{data.nginx.doc_root}}/{{data.nginx.nagvis.web_directory}}
    - target: /usr/share/nagvis/share
    - watch:
      - file: nagvis-www-dir
    - watch_in:
      - mc_proxy: nagvis-pre-install


