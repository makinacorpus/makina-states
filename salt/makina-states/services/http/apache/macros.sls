{# Apache specific macros:
# - extend_switch_mpm
# - virtualhost
# - minimal_index
#}
{% set ugs = salt['mc_usergroup.settings']() %}

{# virtualhost => create all states for a virtualhost:
#   - virtualhost file
#   - include file
#   - a2ensite/dissite commands
#
#   Virtualhost are composed from a basic header content
#   which include the real content of all vhosts.
#   The 2 parts are overridable, but you certainly only need
#   to change the corpse.
#
#   Idea is mostly that giving the following arguments
#   will be sufficient to have your vhost running:
#
#       domain
#           domain name (ServerName)
#       doc_root
#           path to the document root,
#           default is /srv/projects/<site>/www/
#       vh_content_source
#           a jinja template or plain file in the salt
#           file.managed function syntax
#           (salt:// or fullpath) for the corpse
#           (php directives, or proxypass or other stuff)
#           default: http://goo.gl/jB6Ext (github)
#
#   You may also want to set:
#
#       server_aliases
#           a string or a list of strings, theses are the
#           alternate names of this site
#       Any other keyword argument (kwarg/kwargs)
#           extra variables to load for virtualvhost templates
#           rendering or any kwarg to mc_apache.vhost_settings
#
# Please look at mc_apache.vhost_settings if you want
# to tweak more the macro call to fit your needs
# if any are not fulfilled
# by default.
#
#}
{% macro virtualhost(domain, doc_root) %}
{% set data = salt['mc_apache.vhost_settings'](domain, doc_root, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
{% set project = data.project %}
{% set vh_template_source = data.vh_template_source%}
{% set vh_content_source = data.vh_content_source%}
{% set vh_in_template_source = data.vh_content_source%}
{% set vh_top_source = data.vh_top_source%}
{% set active = data.active %}
{% set avhost = data.avhost %}
{% set evhost = data.evhost %}
{% set ivhost = data.ivhost %}
{% set ivhosttop = data.ivhosttop %}

{% for k in ['ssl_bundle', 'ssl_key', 'ssl_cert', 'ssl_cacert'] %}
{% set ssld = data.get(k, '') %}
{% if ssld %}
makina-apache-virtualhost-{{ project }}-ssl-{{k}}:
  file.managed:
    - user: www-data
    - group: root
    - mode: 750
    - name: {{data[k + '_path']}}
    - contents: |
                {{salt['mc_utils.indent'](ssld, 16)}}
    - makedirs: true
    - watch:
      - mc_proxy: makina-apache-vhostconf
      - file: {{ project }}-makina-apache-virtualhost-content
    - watch_in:
      - mc_proxy: makina-apache-post-conf
{% endif %}
{% endfor %}

{#- Virtualhost basic file including the vhost with the content in it's body #}
{{ project }}-makina-apache-virtualhost:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{data.avhost}}.conf
    - source: {{vh_template_source}}
    - template: "jinja"
    - defaults:
        data: |
              {{sdata}}
    - watch:
      - mc_proxy: makina-apache-vhostconf
      - file: {{ project }}-makina-apache-virtualhost-content
    - watch_in:
      - mc_proxy: makina-apache-post-conf

{# Virtualhost real content, shared by SSL and non-SSL virtualhosts #}
{{ project }}-makina-apache-virtualhost-top:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ ivhosttop }}.conf
    - source: {{vh_top_source}}
    - template: "jinja"
    - defaults:
        data: |
              {{sdata}}
    - watch:
      - mc_proxy: makina-apache-vhostconf
    - watch_in:
      - mc_proxy: makina-apache-post-conf

{{ project }}-makina-apache-virtualhost-content:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ ivhost }}.conf
    - source: {{vh_content_source}}
    - template: "jinja"
    - defaults:
        data: |
              {{sdata}}
    - watch:
      - mc_proxy: makina-apache-vhostconf
    - watch_in:
      - mc_proxy: makina-apache-post-conf

{% if not active %}
{{project}}-makina-apache-virtualhost-remove-short-and-non-active:
  file.absent:
    - names:
      - {{evhost}}
      - {{evhost}}.conf
    - watch_in:
      - mc_proxy: makina-apache-post-conf
{% endif%}
{% if active %}
{{project}}-makina-apache-virtualhost-status:
  file.symlink:
    - target: {{avhost}}.conf
    - name: {{evhost}}.conf
    - watch:
      - file: {{ project }}-makina-apache-virtualhost
    - watch_in:
      - mc_proxy: makina-apache-post-conf
{% endif %}
{% endmacro %}

{# Macros helpers used in state to switch from one mpm to another #}
{% set apacheSettings = salt['mc_apache.settings']() %}
{% macro other_mpm_pkgs(mpm, indent='') %}
{% set opkgs = [] %}
{% for dmpm, packages in apacheSettings['mpm-packages'].items() %}
{%  if mpm != dmpm %}
{%    for pkg in packages %}{{indent}}      - {{pkg}}
{%    endfor %}
{%  endif %}
{% endfor %}
{% endmacro %}

{# LEFT OVER FOR RETROCOMPAT #}
{% macro mpm_pkgs(mpm, indent='') %}{#
DISABLED USE MAKINA-STATES settings
{% set pkgs = apacheSettings['mpm-packages'].get(mpm, [] ) %}
{% for pkg in pkgs -%}{{indent}}      - {{ pkg }}
{% endfor -%}
#}{% endmacro %}

{# exposed macro to switch the mpm #}
{# LEFT OVER FOR RETROCOMPAT #}
{% macro extend_switch_mpm(mpm) %}{#{#
DISABLED USE MAKINA-STATES settings
  apache-uninstall-others-mpms:
    pkg.removed:
      - pkgs:
        {{ other_mpm_pkgs(mpm, indent='  ') }}
  apache-mpm:
    pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
      - pkgs:
        {{ mpm_pkgs(mpm, indent='  ') }}
  makina-apache-main-conf:
    mc_apache.deployed:
      - mpm: {{mpm}}
#}{% endmacro %}

{# Macro dedicated to generate a minimal index.html #}
{% macro minimal_index(doc_root, domain="no domain", mode="unkown mode") %}
{{ doc_root }}-minimal-index:
  file.managed:
    - name: {{ doc_root }}/index.html
    - unless: test -e "{{ doc_root }}/index.php"
    - source:
    - contents: >
                <html>
                <body>
                It works from {{doc_root.split("/")[-1]}}/{{domain}}/{{mode}}
                </body>
                </html>
    - makedirs: true
    - user: {{apacheSettings.httpd_user}}
    - group: {{ ugs.group }}
    - watch:
      - mc_proxy: postcheckout-project-hook
      - mc_proxy: makina-apache-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-post-conf
{% endmacro %}
{# vim: set nofoldenable :#}
