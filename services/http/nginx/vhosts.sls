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

{% macro virtualhost(site = nginxSettings.default_domain,
                     small_name = None,
                     active = nginxSettings.default_activation,
                     port = nginxSettings.port,
                     documentRoot = nginxSettings.docroot,
                     server_aliases = None,
                     redirect_aliases = nginxSettings.redirect_aliases,
                     allowed_hosts = nginxSettings.allowed_hosts,
                     vh_top_source = nginxSettings.vhost_top_template,
                     vh_template_source = nginxSettings.vhost_wrapper_template,
                     vh_content_source = nginxSettings.vhost_content_template,
                     default_server=False,
                     extra_jinja_nginx_variables = None) %}
{% set small_name = small_name or site.replace('.', '_').replace('-', '_') %}
{% set doc_root = documentRoot or salt['mc_localsettings.settings']()['locations'].projects_dir + site  + '/www' %}
{% set vhost_available_file = nginxSettings.basedir + "/sites-available/" + site + ".conf" %}
{% set vhost_available_content_file = nginxSettings.basedir + "/sites-available/" + site + ".content.conf" %}
{% set vhost_available_top_file = nginxSettings.basedir + "/sites-available/" + site + ".content.conf" %}
{% set vhost_data = {
 'data': nginxSettings,
 'small_name': small_name,
 'port': port,
 'site': site,
 'small_name': small_name,
 'doc_root': doc_root,
 'server_name': site,
 'server_aliases': server_aliases,
 'allowed_hosts': 'allowed_hosts',
 'default_server': False,
 'redirect_aliases': 'redirect_aliases',
} %}
{% do vhost_data.update(extra_jinja_nginx_variables) %}
{% set svhost_data = salt['mc_utils.yaml_dump'](vhost_data) %}

# Virtualhost basic file
makina-nginx-virtualhost-{{ small_name }}:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: {{ vhost_available_top_file }}
    - source: {{ vh_top_source }}
    - template: 'jinja'
    - makedirs: true
    - defaults: "{{svhost_data}}"
    - watch_in:
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
    - template: 'jinja'
    - makedirs: true
    - defaults: "{{svhost_data}}"
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

makina-nginx-virtualhost-{{ small_name }}-content:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: {{ vhost_available_content_file}}
    - source: {{ vh__content_source }}
    - template: 'jinja'
    - makedirs: true
    - defaults: "{{svhost_data}}"
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

{{ toggle_vhost(site, active=active) }}
{% endmacro %}
{{ virtualhost(
    'default', default', default_domains=data.default_domains,, default_server=True,
    vh_content_source=data.vhost_default_content)}}

{% for site,siteDef in salt['mc_nginx.settings']().get('virtualhosts', {}).items() %}
{%   do siteDef.update({'site': site}) %}
{{   virtualhost(**siteDef) }}
{% endfor %}
