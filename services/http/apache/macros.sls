{# Apache specific macros:
# - extend_switch_mpm
# - virtualhost
# - minimal_index
#}
{% set ugs = salt['mc_usergroup.settings']() %}
{% set nodetypes_reg = salt['mc_nodetypes.registry']() %}
{% set apacheSettings = salt['mc_apache.settings']() %}
{% set apacheData = apacheSettings %}
{% set default_vh_template_source = apacheSettings.default_vh_template_source %}
{% set default_vh_in_template_source = apacheSettings.default_vh_in_template_source %}

{# Macros helpers used in state to switch from one mpm to another #}
{% macro other_mpm_pkgs(mpm, indent='') %}
{% set opkgs = [] %}
{% for dmpm, packages in apacheSettings['mpm-packages'].items() %}
{%  if mpm != dmpm %}
{%    for pkg in packages %}{{indent}}      - {{pkg}}
{%    endfor %}
{%  endif %}
{% endfor %}
{% endmacro %}

{% macro mpm_pkgs(mpm, indent='') %}
{% set pkgs = apacheSettings['mpm-packages'].get(mpm, [] ) %}
{% for pkg in pkgs -%}{{indent}}      - {{ pkg }}
{% endfor -%}
{% endmacro %}

{# exposed macro to switch the mpm #}
{% macro extend_switch_mpm(mpm) %}
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
{% endmacro %}

{# * virtualhost => create all states for a virtualhost (virtualhost file, include file, a2ensite/dissite command
#
#   Idea is that we also feed this macro with a least
#
#     - a template for the virtualhost global directives, 
#       you will in most cases use the providen one
#     - a template for the corpse (php directives, or 
#       proxypass or other stuff), this is what you ll write
#
#   The args to the macros are:
#
#   - domain
#       domain name (ServerName)
#   - number
#       Virtualhost priority number (for apache), without a default VH the first one became the default virtualhost
#   - serveradmin_mail
#       data that may be used on error page, default is webmaster@<site-name>
#   - server_aliases
#       a string or a list of strings, theses are the alternate names of this site
#   - doc_root
#       path to the document root, default is /srv/projects/<site>/www/
#   - redirect_aliases
#       True by default, make a special Virtualhost with all server_aliases, all redirecting
#       with a 301 to the site name, better for SEO. But you may need real server_aliases
#       for static parallel file servers, for example, then set that to True.
#   - allow_htaccess
#       False by default, if your project use .htaccess files, then prey for your soul,
#       eat some shit, kill yourself and set that to True
#   - vh_template_source
#       source (jinja) of the file.managed for the vhirtualhost template
#       default http://goo.gl/RFgkHE (github)
#   - vh_in_template_source
#       source (jinja) of the file.managed for the vhirtualhost included content
#       (the most important part when making alterations of vh content); default:
#       default http://goo.gl/jB6Ext (github)
#   - extra_jinja_apache_variables
#       extra variables to load for virtualvhost templates rendering
#   - log_level
#       log level
#   - [ssl_]interface
#       interface of the namevirtualhost (like in "*:80"), default is "*"
#   - [ssl_]port
#       port of the namevirtualhost (like in "*:80"), default is "80" and "443" for ssl version
#   - active
#       True by default, set to False to disable the Virtualhost
#   - project
#       site nickname, used in states and log files, if not given it will be build from site name
#}
{% macro virtualhost(domain="example.com",
                     number="100",
                     serveradmin_mail=None,
                     server_aliases=None,
                     extra_jinja_apache_variables=None,
                     vh_template_source=default_vh_template_source,
                     vh_in_template_source=default_vh_in_template_source,
                     log_level="warn",
                     interface="*",
                     ssl_interface="*",
                     port="80",
                     ssl_port="443",
                     redirect_aliases=True,
                     allow_htaccess=False,
                     active=True,
                     project=None,
                     mode="production",
                     project_root=None,
                     doc_root=None) %}
{% set project = salt["mc_project.gen_id"](project or domain) %}
{% set admin_mail = serveradmin_mail or "webmaster@{0}".format(domain) %}
{% set doc_root = salt["mc_project.doc_root"](doc_root=doc_root,
                                              domain=domain,
                                              project_root=project_root,
                                              project=project) %}
{% if not extra_jinja_apache_variables %}
{%  set extra_jinja_apache_variables = {} %}
{% endif %}
{% if not server_aliases %}
{%  set server_aliases = [] %}
{% endif %}
{% set server_aliases = salt["mc_project.server_aliases"](server_aliases) %}
{% set old_mode = (grains["lsb_distrib_id"] == "Ubuntu"
                   and grains["lsb_distrib_release"] < 13.10)
                   or (grains["lsb_distrib_id"] == "Debian"
                       and grains["lsb_distrib_release"] <= 7.0) %}

{% if nodetypes_reg.is.devhost %}
{%  set mode="dev" %}
{% endif %}

{% set evhost = "{basedir}/{number}-{domain}".format(**dict(
  number=number, basedir=apacheSettings.evhostdir, domain=domain)) %}
{% set avhost = "{basedir}/{number}-{domain}".format(**dict(
  number=number, basedir=apacheSettings.vhostdir, domain=domain)) %}

{#- Virtualhost basic file including the vhost with the content in it's body #}
{{ project }}-makina-apache-virtualhost:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ apacheSettings.vhostdir }}/{{ number }}-{{ domain }}.conf
    - source: {{ vh_template_source }}
    - template: "jinja"
    - defaults:
        log_level: "{{ log_level }}"
        serveradmin_mail: "{{ admin_mail }}"
        project: "{{ project }}"
        document_root: "{{ doc_root }}"
        server_name: "{{ domain }}"
        server_aliases: |
                        {{salt['mc_utils.json_dump'](server_aliases)}}
        redirect_aliases: {{ redirect_aliases }}
        interface: "{{ interface }}"
        port: "{{ port }}"
        extra: |
               {{salt['mc_utils.json_dump'](extra_jinja_apache_variables)}}
        mode: {{mode}}
    - watch:
      - mc_proxy: makina-apache-vhostconf
    - watch_in:
      - mc_proxy: makina-apache-post-conf

{# Virtualhost real content, shared by SSL and non-SSL virtualhosts #}
{{ project }}-makina-apache-virtualhost-content:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ apacheSettings.basedir }}/includes/{{ domain }}.conf
    - source: {{ vh_in_template_source }}
    - template: "jinja"
    - defaults:
        mode: {{mode}}
        document_root: {{ doc_root }}
        allow_htaccess: {{ allow_htaccess }}
        extra: |
               {{salt['mc_utils.json_dump'](extra_jinja_apache_variables)}}
    - watch:
      - mc_proxy: makina-apache-vhostconf
    - watch_in:
      - mc_proxy: makina-apache-post-conf

{{project}}-makina-apache-virtualhost-remove-short-and-non-active:
  file.absent:
    - names:
      - {{evhost}}
      {% if not active %}
      - {{evhost}}.conf
      {% endif%}
    - watch_in:
      - mc_proxy: makina-apache-post-conf

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

{# Macro dedicated to GENERATE a minimal index.html #}
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
