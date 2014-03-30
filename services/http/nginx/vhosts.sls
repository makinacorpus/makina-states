include:
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.nginx.services

{#
# Virtualhosts, here are the ones defined in pillar, if any
# We loop on VH defined in pillar nginx/virtualhosts, check the
# macro definition for the pillar dictionnary keys available. The
# virtualhosts key is set as the site name, and all keys are then
# added.
# pillar example:
# makina-states.services.http.nginx.virtualhosts.example.com:
#     active: False
#     small_name: example
#     documentRoot: /srv/foo/bar/www
# makina-states.services.http.nginx.virtualhosts.example.foo.com:
#     active: False
#     port: 8080
#     server_aliases:
#       - bar.foo.com
#
# Note that the best way to make a VH is not the pillar, but
# loading the macro as we do here and use virtualhost()) call
# in a state.
# Then use the pillar to alter your default parameters given to this call
#}
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
                     vh_template_source = nginxSettings.vhost_wrapper_template,
                     extra_jinja_nginx_variables = None) %}
{% set small_name = small_name or site.replace('.', '_').replace('-', '_') %}
{% set doc_root = documentRoot or salt['mc_localsettings.settings']()['locations'].projects_dir + site  + '/www' %}
{% set vhost_available_file = nginxSettings.basedir + "/sites-available/" + site + ".conf" %}

# Virtualhost basic file
makina-nginx-virtualhost-{{ small_name }}:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: {{ vhost_available_file }}
    - source: {{ vh_template_source }}
    - template: 'jinja'
    - makedirs: true
    - defaults:
        small_name: "{{ small_name }}"
        document_root: "{{ doc_root }}"
        server_name: "{{ site }}"
        {% if server_aliases %}
        server_aliases:
          {% for server_alias in server_ali
        allowed_hosts:
          {% for allowed_host in allowed_hosts %}
          - {{ allowed_host }}
          {% endfor %}
        {% endif %}
        redirect_aliases: {{ redirect_aliases }}
        port: "{{ port }}"
{% if extra_jinja_nginx_variables %}
{% for variablename,variablevalue in extra_jinja_nginx_variables.items() %}
        {{ variablename }}: "{{ variablevalue }}"
{% endfor %}
{% endif %}
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

{{ toggle_vhost(site, active=active) }}

{% endmacro %}

{% for site,siteDef in salt['mc_nginx.settings']().get('virtualhosts', {}).items() -%}
{%   do siteDef.update({'site': site}) -%}
{{   virtualhost(**siteDef) -}}
{% endfor -%}
