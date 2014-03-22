{#- Common php installations (mod_php or php-fpm) files #}
{% import "makina-states/services/http/apache.sls" as apache with context %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set nodetypes_registry = salt['mc_nodetypes.registry']() %}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set phpSettings = salt['mc_php.settings']()  %}
{% set s_ALL = phpSettings.s_ALL %}
{% set apacheSettings = salt['mc_apache.settings']() %}

{% macro do(full=False) %}

makina-php-timezone:
  file.managed:
    - user: root
    - group: root
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

#--------------------- APC (mostly deprecated)
{% if phpSettings.modules.apc.install %}
makina-php-apc:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ phpSettings.confdir }}/apcu.ini
    - source: salt://makina-states/files{{ phpSettings.confdir }}/apcu.ini
    - template: 'jinja'
    - defaults:
        enabled: {{ phpSettings.modules.apc.enabled }}
        enable_cli: {{ phpSettings.modules.apc.enable_cli }}
        shm_segments: "{{ phpSettings.modules.apc.shm_segments }}"
        shm_size: "{{ phpSettings.modules.apc.shm_size }}"
        mmap_file_mask: "{{ phpSettings.modules.apc.mmap_file_mask }}"
    - require:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-conf

{% if full and not (
    (grains['os'] in 'Ubuntu')
    and (localsettings.udist not in ['precise'])
) %}
{%   if phpSettings.modules.apc.enabled %}
makina-php-apc-install:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5enmod {{s_ALL}} apcu
    {% if grains['os'] in ['Ubuntu'] %}
    - onlyif: test -e {{ locs.sbin_dir }}/php5enmod
    - unless: {{ locs.sbin_dir }}/php5query -q -s cli -m apcu
    {% endif %}
    - require:
      - mc_proxy: makina-php-pre-conf
      - file: makina-php-apc
    - watch_in:
      - mc_proxy: makina-php-post-conf
{%   else %}
makina-php-apc-disable:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5dismod {{s_ALL}} apcu
    {% if grains['os'] in ['Ubuntu'] %}
    - onlyif: {{ locs.sbin_dir }}/php5query -q -s cli -m apcu
    {% endif %}
    - unless: test ! -e {{ locs.sbin_dir }}/php5enmod
    - require:
      - mc_proxy: makina-php-pre-conf
      - file: makina-php-apc
    - watch_in:
      - mc_proxy: makina-php-post-conf
{%   endif %}
{% endif %}

#--------------------- XDEBUG
{% if phpSettings.modules.xdebug.install %}
{%   if phpSettings.modules.xdebug.enabled %}
makina-php-xdebug-install:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5enmod {{s_ALL}} xdebug
    {% if grains['os'] in ['Ubuntu'] %}
    - unless: {{ locs.sbin_dir }}/php5query -q -s cli -m xdebug
    {% endif %}
    - onlyif: test -e {{ locs.sbin_dir }}/php5enmod
    - require:
      - mc_proxy: makina-php-pre-conf
    - watch_in:
      - mc_proxy: makina-php-post-conf
{%   else %}
makina-php-xdebug-disable:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5dismod {{s_ALL}} xdebug
    {% if grains['os'] in ['Ubuntu'] %}
    - onlyif: {{ locs.sbin_dir }}/php5query -q -s cli -m xdebug
    {% endif %}
    - unless: test ! -e {{ locs.sbin_dir }}/php5enmod
    - require:
      - mc_proxy: makina-php-pre-conf
    - watch_in:
      - mc_proxy: makina-php-post-conf
{%   endif %}
{% endif %}
{% endif %}
{%endmacro%}
{{do(full=False)}}
