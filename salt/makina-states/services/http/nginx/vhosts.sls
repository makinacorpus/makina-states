{% set nginxSettings = salt['mc_nginx.settings']() %}
{% import "makina-states/services/http/nginx/macros.sls" as nginx with context %}

{# retro compat #}
{% set virtualhost = nginx.virtualhost %}
{% set toggle_virtualhost = nginx.toggle_virtualhost %}

include:
  - makina-states.services.http.common.default_vhost
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.nginx.services
nginx-remove-def:
  file.absent:
    - name: /etc/nginx/sites-enabled/default
    - require:
      - mc_proxy: nginx-pre-conf-hook
    - require_in:
      - mc_proxy: nginx-post-conf-hook


{% if nginxSettings.default_vhost %}
{{ nginx.virtualhost(
    'localhost',
    doc_root=nginxSettings.doc_root,
    default_server=True,
    vh_content_source=nginxSettings.vhost_default_content)}}
{% else %}
removedef-nginx-test:
  file.absent:
    - name: /etc/nginx/sites-enabled/localhost.conf
    - watch_in:
      - mc_proxy: nginx-pre-restart-hook
    - watch:
      - mc_proxy: nginx-post-conf-hook
{% endif %}


{% for site, siteDef in salt['mc_nginx.settings']().get('virtualhosts', {}).items() %}
{%   do siteDef.update({'domain': site}) %}
{{   virtualhost(**siteDef) }}
{% endfor %}
