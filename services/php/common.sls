{#- Common php installations (mod_php or php-fpm) files #}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{% set phpSettings = services.phpSettings %}

{% macro apache_includes(full=True) %}
{% if full %}
  - makina-states.services.http.apache
{% else %}
  - makina-states.services.http.apache-standalone
{% endif %}
  - makina-states.services.php.php-apache-hooks
{% endmacro %}

{% macro includes(full=True) %}
{% if grains.get('lsb_distrib_id','') == "Debian" %}
  - makina-states.services.php.php-hooks
   # Include dotdeb repository for Debian
  - makina-states.localsettings.repository_dotdeb
{% endif %}
{% endmacro %}

{% macro apache_hooks(full=True) %}
{% if full %}
{% if grains.get('lsb_distrib_id','') == "Debian" %}
dotdeb-apache-makina-apache-php-pre-inst:
  mc_dummy.dummy:
    - require:
      - pkgrepo: dotdeb-repo
    - watch_in:
      - mc_dummy: makina-apache-php-pre-inst
{% endif %}
{% endif %}
{% endmacro %}

{% macro do(full=True) %}
{% if grains.get('lsb_distrib_id','') == "Debian" %}
dotdeb-makina-apache-php-pre-inst:
  mc_dummy.dummy:
    - require:
      - pkgrepo: dotdeb-repo
    - watch_in:
      - mc_dummy: makina-php-pre-inst
{% endif %}

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
      - mc_dummy: makina-php-post-inst
    - watch_in:
      - mc_dummy: makina-php-pre-conf

{% set s_ALL = phpSettings.s_ALL %}


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
      - mc_dummy: makina-php-post-inst
    - watch_in:
      - mc_dummy: makina-php-pre-conf

{%   if phpSettings.modules.apc.enabled %}
makina-php-apc-install:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5enmod {{s_ALL}} apcu
    {% if grains['os'] in ['Ubuntu'] %}
    - unless: {{ locs.sbin_dir }}/php5query -q -s cli -m apcu
    {% endif %}
    - require:
      - mc_dummy: makina-php-pre-conf
      - file: makina-php-apc
    - watch_in:
      - mc_dummy: makina-php-post-conf
{%   else %}
makina-php-apc-disable:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5dismod {{s_ALL}} apcu
    {% if grains['os'] in ['Ubuntu'] %}
    - onlyif: {{ locs.sbin_dir }}/php5query -q -s cli -m apcu
    {% endif %}
    - require:
      - mc_dummy: makina-php-pre-conf
      - file: makina-php-apc
    - watch_in:
      - mc_dummy: makina-php-post-conf
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
    - require:
      - mc_dummy: makina-php-pre-conf
    - watch_in:
      - mc_dummy: makina-php-post-conf
{%   else %}
makina-php-xdebug-disable:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5dismod {{s_ALL}} xdebug
    {% if grains['os'] in ['Ubuntu'] %}
    - onlyif: {{ locs.sbin_dir }}/php5query -q -s cli -m xdebug
    {% endif %}
    - require:
      - mc_dummy: makina-php-pre-conf
    - watch_in:
      - mc_dummy: makina-php-post-conf
{%   endif %}
{% endif %}
{% endmacro %}
{{ do(full=False) }}
