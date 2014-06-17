{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_icinga_cgi.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/cgi/uwsgi/init.sls" as uwsgi with context %}
include:
  - makina-states.services.http.nginx
  - makina-states.services.cgi.uwsgi

# copy configuration
#icinga_cgi-copy-configuration:
#  file.managed:

# create a virtualhost in nginx
{{ nginx.virtualhost(domain=data.nginx.virtualhost,
                     doc_root=data.nginx.doc_root,

                     vh_content_source=data.nginx.vh_content_source,
                     vh_top_source=data.nginx.vh_top_source,
                     cfg=data.nginx.vh_content_source)}}

# configure uwsgi
{{ uwsgi.app(name=data.uwsgi.name,
             config_file=data.uwsgi.config_file,
             config_data=data.uwsgi.config_data,
             enabled=data.uwsgi.enabled) }}
