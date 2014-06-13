{% set locs = salt['mc_locations.settings']() %}
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

                     vh_content_source="salt://makina-states/files/etc/icinga-web/nginx.conf",
                     vh_top_source="salt://makina-states/files/etc/icinga-web/nginx.top.conf",
                     cfg="salt://makina-states/files/etc/icinga-web/nginx.conf")}}

# add a pool php-fpm
{{php.fpm_pool(data.nginx.virtualhost, data.nginx.doc_root, **data.phpfpm)}}
