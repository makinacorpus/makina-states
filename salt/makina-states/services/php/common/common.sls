{% set locs = salt['mc_locations.settings']() %}
{% set phpSettings = salt['mc_php.settings']()  %}
{% set pkgssettings = salt['mc_pkgs.settings']()  %}
{% set s_ALL = phpSettings.s_all %}
{% import "makina-states/services/php/macros.sls" as macros with context %}

{#- Common php installations (mod_php or php-fpm) files #}
include:
  - makina-states.services.php.hooks
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
{% elif grains['os'] in ['Ubuntu'] and grains['osrelease'] < '16.04' %}
makina-php-repos:
  pkgrepo.managed:
    - humanname: php ppa
    - name: deb http://ppa.launchpad.net/ondrej/php5-{{phpSettings.ppa_ver}}/ubuntu {{pkgssettings.ppa_dist}} main
    - dist: {{pkgssettings.ppa_dist}}
    - file: /etc/apt/sources.list.d/phpppa.list
    - keyid: E5267A6C
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: makina-php-pre-repo
    - watch_in:
      - mc_proxy: makina-php-repos
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

php-cli:
  pkg.installed:
    - pkgs:
      - {{phpSettings.packages.cli}}
    - watch:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - mc_proxy: makina-php-post-inst

phpservice-systemd-override-dir:
  file.directory:
    - makedirs: true
    - user: root
    - group: root
    - mode: 775
    - names:
      - /etc/systemd/system/{{ phpSettings.service }}.service.d
    - require:
      - mc_proxy: makina-php-post-inst

phpservice-systemd-config-override:
  file.managed:
    - user: root
    - group: root
    - makedirs: true
    - mode: 664
    - name: /etc/systemd/system/{{ phpSettings.service }}.service.d/override.conf
    - source: salt://makina-states/files/etc/systemd/system/overrides.d/php.conf
    - template: 'jinja'
    - require:
      - mc_proxy: makina-php-post-inst
      - file: phpservice-systemd-override-dir
    - watch_in:
      - mc_proxy: makina-php-pre-conf

phpservice-systemd-reload-conf:
  cmd.run:
    - name: "systemctl daemon-reload"
    - onchanges:
      - file: phpservice-systemd-config-override


makina-php-timezone:
  file.managed:
    - user: root
    - group: root
    - makedirs: true
    - mode: 664
    - name: {{ phpSettings.confdir }}/timezone.ini
    - source: salt://makina-states/files{{ phpSettings.confdir }}/timezone.ini
    - template: 'jinja'
    - defaults:
        timezone: "{{ phpSettings.timezone }}"
    - require:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-conf

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

{% if phpSettings.opcache_install %}
makina-php-opcache:
  file.managed:
    - user: root
    - makedirs: true
    - group: root
    - mode: 664
    - name: {{ phpSettings.confdir }}/opcache.ini
    - source: salt://makina-states/files{{ phpSettings.confdir }}/opcache.ini
    - template: 'jinja'
    - require:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-conf
{% endif %}

#--------------------- APC (mostly deprecated)
{% if phpSettings.apc_install %}
makina-php-apc:
  file.managed:
    - user: root
    - makedirs: true
    - group: root
    - mode: 664
    - name: {{ phpSettings.confdir }}/apcu.ini
    - source: salt://makina-states/files{{ phpSettings.confdir }}/apcu.ini
    - template: 'jinja'
    - defaults:
        enabled: {{ phpSettings.apc_enabled }}
        enable_cli: {{ phpSettings.apc_enable_cli }}
        shm_segments: "{{ phpSettings.apc_shm_segments }}"
        shm_size: "{{ phpSettings.apc_shm_size }}"
        mmap_file_mask: "{{ phpSettings.apc_mmap_file_mask }}"
    - require:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-conf

{% if not ( (grains['os'] in 'Ubuntu') and (salt['mc_pkgs.settings']().udist not in ['precise'])) %}
{{ macros.toggle_ext('apcu', apc_enabled)}}
{% endif %}
{% endif %}
