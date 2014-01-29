#
# Common php installations (mod_php or php-fpm) files
#

{% import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'php.common') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{% set phpSettings = services.phpSettings %}

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
      - pkg: makina-php-pkgs
    - watch_in:
      - service: makina-php-reload

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
      - pkg: makina-php-pkgs
    - watch_in:
      - service: makina-php-reload

{%   if phpSettings.modules.apc.enabled %}
makina-php-apc-install:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5enmod -s ALL apcu
    - unless: {{ locs.sbin_dir }}/php5query -q -s cli -m apcu
    - require:
      - pkg: makina-php-pkgs
      - file: makina-php-apc
    - watch_in:
      - service: makina-php-restart
{%   else %}
makina-php-apc-disable:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5dismod -s ALL apcu
    - onlyif: {{ locs.sbin_dir }}/php5query -q -s cli -m apcu
    - require:
      - pkg: makina-php-pkgs
      - file: makina-php-apc
    - watch_in:
      - service: makina-php-restart
{%   endif %}
{% endif %}

#--------------------- XDEBUG
{% if phpSettings.modules.xdebug.install %}
{%   if phpSettings.modules.xdebug.enabled %}
makina-php-xdebug-install:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5enmod -s ALL xdebug
    - unless: {{ locs.sbin_dir }}/php5query -q -s cli -m xdebug
    - require:
      - pkg: makina-php-pkgs
    - watch_in:
      - service: makina-php-restart
{%   else %}
makina-php-xdebug-disable:
  cmd.run:
    - name: {{ locs.sbin_dir }}/php5dismod -s ALL xdebug
    - onlyif: {{ locs.sbin_dir }}/php5query -q -s cli -m xdebug
    - require:
      - pkg: makina-php-pkgs
    - watch_in:
      - service: makina-php-restart
{%   endif %}
{% endif %}

# flag to auto-install as-soon-as-included once
makina-states.services.php.common:
  grains.present:
    - value: True
