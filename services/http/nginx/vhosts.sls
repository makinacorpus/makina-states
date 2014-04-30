include:
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.nginx.services

{% set nginxSettings = salt['mc_nginx.settings']() %}

{% macro toggle_vhost(site, active=True) %}
# Virtualhost status
makina-nginx-virtualhost-{{ site }}-status:
{% set vhost_available_file = nginxSettings.basedir + "/sites-available/" + site + ".conf" %}
{% set vhost_enabled_file = nginxSettings.basedir + "/sites-enabled/" + site + ".conf" %}
  cmd.run:
{% if active %}
    - name: ln -s {{ vhost_available_file }} {{ vhost_enabled_file }}
    - unless: ls {{ vhost_enabled_file }}
{% else %}
    - name: rm -f {{ vhost_enabled_file }}
    - onlyif: ls {{ vhost_enabled_file }}
{% endif %}
    - watch_in:
       - mc_proxy: nginx-post-conf-hook
    - watch_in:
       - mc_proxy: nginx-pre-restart-hook
{% endmacro %}

{% macro virtualhost(domain,
                     small_name=None,
                     active=nginxSettings.default_activation,
                     port=nginxSettings.port,
                     doc_root=nginxSettings.doc_root,
                     server_aliases=None,
                     loglevel=nginxSettings.loglevel,
                     redirect_aliases=nginxSettings.redirect_aliases,
                     allowed_hosts=nginxSettings.allowed_hosts,
                     vh_top_source=nginxSettings.vhost_top_template,
                     vh_template_source=nginxSettings.vhost_wrapper_template,
                     vh_content_source=nginxSettings.vhost_content_template,
                     default_server=False,
                     extra = None,
                     real_ip_header=nginxSettings.real_ip_header,
                     reverse_proxy_addresses=nginxSettings.reverse_proxy_addresses) %}
{% set small_name = small_name or domain.replace('.', '_').replace('-', '_') %}
{% set vhost_available_file = nginxSettings.basedir + "/sites-available/" + domain + ".conf" %}
{% set vhost_available_content_file = nginxSettings.basedir + "/sites-available/" + domain + ".content.conf" %}
{% set vhost_available_top_file = nginxSettings.basedir + "/sites-available/" + domain + ".top.conf" %}
{% set vhost_data = {
 'vhost_top_file': vhost_available_top_file,
 'vhost_content_file': vhost_available_content_file,
 'data': nginxSettings,
 'small_name': small_name,
 'port': port,
 'loglevel': loglevel,
 'real_ip_header': real_ip_header,
 'reverse_proxy_addresses': reverse_proxy_addresses,
 'v6': False,
 'small_name': small_name,
 'doc_root': doc_root,
 'server_name': domain,
 'server_aliases': server_aliases,
 'allowed_hosts': allowed_hosts,
 'default_server': False,
 'redirect_aliases': 'redirect_aliases',
} %}
{% set extra= extra or {} %}
{% do vhost_data.update({'extra':extra}) %}
{% set svhost_data =salt['mc_utils.json_dump'](vhost_data) %}

# Virtualhost basic file
makina-nginx-virtualhost-{{ small_name }}-top:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: {{ vhost_available_top_file }}
    - source: {{ vh_top_source }}
    - template: jinja
    - makedirs: true
    - defaults:
      data: |
            {{svhost_data}}
    - watch:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

makina-nginx-virtualhost-{{ small_name }}:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: {{ vhost_available_file }}
    - source: {{ vh_template_source }}
    - template: jinja
    - makedirs: true
    - defaults:
      data: |
            {{svhost_data}}
    - watch:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

makina-nginx-virtualhost-{{ small_name }}-content:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: {{ vhost_available_content_file}}
    - source: {{ vh_content_source }}
    - template: jinja
    - makedirs: true
    - defaults:
      data: |
            {{svhost_data}}
    - watch:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

{{ toggle_vhost(domain, active=active) }}
{% endmacro %}
nginx-remove-def:
  file.absent:
    - name: /etc/nginx/sites-enabled/default
    - watch:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

{{ virtualhost('localhost',
                default_server=True,
                vh_content_source=nginxSettings.vhost_default_content)}}
{% for site, siteDef in salt['mc_nginx.settings']().get('virtualhosts', {}).items() %}
{%   do siteDef.update({'domain': site}) %}
{{   virtualhost(**siteDef) }}
{% endfor %}
