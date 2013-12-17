#
# Common php instalations (mod_php or php-fpm) files
#

# Load defaults values -----------------------------------------
{% from 'makina-states/services/php/php_defaults.jinja' import phpData with context %}

{% import "makina-states/_macros/services.jinja" as services with context %}
{{ services.register('php.common') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}

makina-php-timezone:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ phpData.confdir }}/timezone.ini
    - source: salt://makina-states/files{{ phpData.confdir }}/timezone.ini
    - template: 'jinja'
    - defaults:
        timezone: "{{ phpData.timezone }}"
    - require:
      - pkg: makina-php-pkgs
    - watch_in:
      - service: makina-php-reload

#--------------------- APC (mostly deprecated)
{% if phpData.modules.apc.install %}
makina-php-apc:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ phpData.confdir }}/apcu.ini
    - source: salt://makina-states/files{{ phpData.confdir }}/apcu.ini
    - template: 'jinja'
    - defaults:
        enabled: {{ phpData.modules.apc.enabled }}
        enable_cli: {{ phpData.modules.apc.enable_cli }}
        shm_segments: "{{ phpData.modules.apc.shm_segments }}"
        shm_size: "{{ phpData.modules.apc.shm_size }}"
        mmap_file_mask: "{{ phpData.modules.apc.mmap_file_mask }}"
    - require:
      - pkg: makina-php-pkgs
    - watch_in:
      - service: makina-php-reload

{%   if phpData.modules.apc.enabled %}
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
{% if phpData.modules.xdebug.install %}
{%   if phpData.modules.xdebug.enabled %}
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
makina.services.php.common:
  grains.present:
    - value: True
