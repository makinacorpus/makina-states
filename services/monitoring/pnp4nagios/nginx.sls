{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_pnp4nagios.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/php/init.sls" as php with context %}

include:
  - makina-states.services.php.phpfpm_with_nginx
  - makina-states.services.http.nginx
  - makina-states.services.monitoring.pnp4nagios.hooks

# create a virtualhost in nginx
{{ nginx.virtualhost(**data.nginx)}}

# add a pool php-fpm
{{php.fpm_pool(domain=data.nginx.domain, **data.phpfpm)}}

# install php5 dependancies
pnp4nagios-php5-deps:
  pkg.{{pkgssettings['installmode']}}:
    - watch_in:
      - mc_proxy: pnp4nagios-pre-install
    - pkgs:
      {% for package in data.phpfpm.extensions_packages %}
      - {{package}}
      {% endfor %}



