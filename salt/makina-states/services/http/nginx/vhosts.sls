{% set nginxSettings = salt['mc_nginx.settings']() %}
{% import "makina-states/services/http/nginx/macros.sls" as nginx with context %}

{# retro compat #}
{% set virtualhost = nginx.virtualhost %}
{% set toggle_virtualhost = nginx.toggle_virtualhost %}

include:
  - makina-states.services.http.common.default_vhost
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.nginx.services
nginx-remove-def1:
  file.absent:
    - name: /etc/nginx/sites-enabled/default
    - require:
      - mc_proxy: nginx-pre-conf-hook
    - require_in:
      - mc_proxy: nginx-post-conf-hook
nginx-remove-def2:
  file.absent:
    - name: /etc/nginx/conf.d/default
    - require:
      - mc_proxy: nginx-pre-conf-hook
    - require_in:
      - mc_proxy: nginx-post-conf-hook


{% if nginxSettings.default_vhost %}
{{ nginx.virtualhost(
    'localhost',
    doc_root=nginxSettings.doc_root,
    default_server=nginxSettings.default_vhost_is_default_server,
    vh_content_source=nginxSettings.vhost_default_content)}}
{% else %}
removedef-nginx-default-test1:
  file.absent:
    - name: /etc/nginx/sites-enabled/localhost.conf
    - watch_in:
      - mc_proxy: nginx-pre-restart-hook
    - watch:
      - mc_proxy: nginx-post-conf-hook
removedef-nginx-default-test2:
  file.absent:
    - name: /etc/nginx/conf.d/localhost.conf
    - watch_in:
      - mc_proxy: nginx-pre-restart-hook
    - watch:
      - mc_proxy: nginx-post-conf-hook
{% endif %}


{% for site, siteDef in salt['mc_nginx.settings']().get('virtualhosts', {}).items() %}
{%   do siteDef.update({'domain': site}) %}
{{   virtualhost(**siteDef) }}
{% endfor %}
