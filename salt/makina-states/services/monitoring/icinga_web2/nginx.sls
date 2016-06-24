{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_icinga_web2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/php/init.sls" as php with context %}

include:
  - makina-states.services.php.phpfpm_with_nginx
  - makina-states.services.http.nginx
  - makina-states.services.monitoring.icinga_web2.hooks

# create a virtualhost in nginx
{{ nginx.virtualhost(**data.nginx)}}

# add a pool php-fpm
{{php.fpm_pool(domain=data.nginx.domain, **data.phpfpm)}}

# install php5-pgsql
icinga_web2-php5-deps:
  pkg.{{pkgssettings['installmode']}}:
    - watch_in:
      - mc_proxy: icinga_web2-pre-install
    - pkgs:
      {% for package in data.phpfpm.extensions_packages %}
      - {{package}}
      {% endfor %}

{% if data.get('users', {}) %}
{% for user, udata in data.users.items() %}
icingaweb2-{{user}}-htaccess:
  webutil.user_exists:
    - name: "{{user}}"
    - password: "{{udata.password}}"
    - htpasswd_file: {{data.htpasswd}}
    - options: m
    - force: true
{% endfor %}
{% endif %}

icingaweb2-htaccess:
  file.managed:
    - name: "{{data.htpasswd}}"
    - source: ''
    - user: www-data
    - group: www-data
    - mode: 770
    - watch:
      - mc_proxy: nginx-post-conf-hook
