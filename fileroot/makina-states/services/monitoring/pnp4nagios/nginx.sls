{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_pnp4nagios.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/php/init.sls" as php with context %}

include:
  - makina-states.services.http.nginx

# create a virtualhost in nginx
{{ nginx.virtualhost(**data.nginx)}}
