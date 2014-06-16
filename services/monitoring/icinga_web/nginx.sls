{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_icinga_web.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/php/init.sls" as php with context %}

include:
  - makina-states.services.php.phpfpm_with_nginx
  - makina-states.services.http.nginx

# copy configuration
#icinga_web-copy-configuration:
#  file.managed:

# create a virtualhost in nginx
{{ nginx.virtualhost(domain=data.nginx.virtualhost,
                     doc_root=data.nginx.doc_root,

                     vh_content_source=data.nginx.vh_content_source,
                     vh_top_source=data.nginx.vh_top_source,
                     cfg="salt://makina-states/files/etc/icinga-web/nginx.conf")}}

# add a pool php-fpm
{{php.fpm_pool(domain=data.nginx.virtualhost,
               doc_root=data.nginx.doc_root,
               open_basedir=data.phpfpm.open_basedir)}}
#               **data.phpfpm)}}

# install php5-pgsql
icinga_web-php5-pgsql:
  pkg.{{pkgssettings['installmode']}}:
    - watch_in:
      - mc_proxy: icinga_web-pre-install
    - pkgs:
      {% for package in data.phpfpm.extensions_packages %}
      - {{package}}
      {% endfor %}
