{% set nginxSettings = salt['mc_nginx.settings']() %}

{#
# like the apache macro (see its doc), you have at least to provide
# the domain and doc_root, and certainly a slug for the vhost defintion.
# You wont need to provide a full virtualhost and you wont !
#
# In other terms, you have to give at least the corpse (template or plain file)
# and maybe the "top" template wich will be included outside the
# servers definitions, to add for example extra upstream servers.
#
# Macros mains args:
#
#     domain
#       domain
#     doc_root
#       document root
#     vh_content_source
#       template rendering the vhost inner content (normmally you will need
#       only to write this one)
#     vh_top_source
#       source outside of server defintions (normmally you may need
#       only to write this one)
#     vh_template_source
#       template rendering the vhost wrapper (http server def)
#       You may not need to override it
#     server_aliases
#       server aliases if any
#
#}
{% macro virtualhost(domain, doc_root=nginxSettings.doc_root) %}
{% set data = salt['mc_nginx.vhost_settings'](domain, doc_root, **kwargs) %}
{% set svhost_data =salt['mc_utils.json_dump'](data) %}
{% set small_name = data.small_name %}

# Virtualhost basic file
makina-nginx-virtualhost-{{ small_name }}-top:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: {{data.vhost_top_file  }}
    - source: {{ data.vh_top_source }}
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
    - name: {{ data.vhost_available_file }}
    - source: {{ data.vh_template_source }}
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
    - name: {{ data.vhost_content_file}}
    - source: {{ data.vh_content_source }}
    - template: jinja
    - makedirs: true
    - defaults:
        data: |
              {{svhost_data}}
    - watch:
      - mc_proxy: nginx-pre-conf-hook
    - watch_in:
      - mc_proxy: nginx-post-conf-hook

{{ toggle_vhost(data.domain, active=data.active) }}
{% endmacro %}


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
 _
