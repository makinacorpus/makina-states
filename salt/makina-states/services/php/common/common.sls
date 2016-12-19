{% import "makina-states/_macros/h.jinja" as h with context %}
{% set locs = salt['mc_locations.settings']() %}
{% set phpSettings = salt['mc_php.settings']()  %}
{% set pkgssettings = salt['mc_pkgs.settings']()  %}
{% set s_ALL = phpSettings.s_all %}
{% import "makina-states/services/php/macros.sls" as macros with context %}

{#- Common php installations (mod_php or php-fpm) files #}
include:
  - makina-states.services.php.hooks
  - makina-states.localsettings.pkgs.fixppas
{%  if grains.get('lsb_distrib_id','') == "Debian" -%}
{# Include dotdeb repository for Debian #}
  - makina-states.localsettings.repository_dotdeb
{%endif %}

{% if grains.get('lsb_distrib_id','') == "Debian" -%}
dotdeb-apache-makina-apache-php-pre-inst:
  mc_proxy.hook:
    - require:
      - mc_proxy: makina-php-pre-repo
      - pkgrepo: dotdeb-repo
    - watch_in:
      - mc_proxy: makina-php-pre-inst
{# Manage php-fpm packages @#}
{% elif phpSettings.use_ppa %}
makina-php-repos:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: php ppa
    - name: deb http://ppa.launchpad.net/ondrej/php/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: /etc/apt/sources.list.d/phpppa.list
    - keyid: E5267A6C
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: makina-php-pre-repo
      - mc_proxy: makina-php-fix-repos
    - watch_in:
      - mc_proxy: makina-php-repos
      - mc_proxy: makina-php-pre-inst
{% else %}
makina-php-repos:
  file.absent:
    - name: /etc/apt/sources.list.d/phpppa.list
    - watch:
      - mc_proxy: makina-php-pre-repo
    - watch_in:
      - mc_proxy: makina-php-pre-inst
  cmd.watch:
    - name: apt-get update
    - watch:
      - file: makina-php-repos
      - mc_proxy: makina-php-pre-repo
    - watch_in:
      - mc_proxy: makina-php-pre-inst
{% endif %}

{% macro rmacro() %}
    - watch:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-conf
{% endmacro %}
{{ h.deliver_config_files(
     phpSettings.get('configs', {}),
     mode='644',
     after_macro=rmacro, prefix='php-')}}

php-cli:
  pkg.installed:
    - pkgs:
      - {{phpSettings.packages.cli}}
    - watch:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - mc_proxy: makina-php-post-inst

#--------------------- APC (mostly deprecated)
makina-php-composer:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: /usr/local/bin/composer
    - unless: /usr/local/bin/composer --version
    - source: '{{phpSettings.composer}}'
    - source_hash: 'sha1={{phpSettings.composer_sha1}}'
    - require:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-conf
  cmd.run:
    - name: /usr/local/bin/composer selfupdate
    - user: root
    - require:
      - file: makina-php-composer
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-conf

{{ macros.toggle_ext('xdebug', phpSettings.xdebug_install and phpSettings.xdebug_enabled) }}

{% if phpSettings.apc_install %}
{% if not ( (grains['os'] in 'Ubuntu') and (salt['mc_pkgs.settings']().udist not in ['precise'])) %}
{{ macros.toggle_ext('apcu', apc_enabled)}}
{% endif %}
{% endif %}