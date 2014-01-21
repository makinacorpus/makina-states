{%- import "makina-states/_macros/services.jinja" as services with context %}
{{- services.register('base.ntp') }}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}

ntp-pkgs:
  pkg.installed:
    - pkgs:
      - ntp
      - tzdata
      - ntpdate

{%- if grains['os'] not in ['Debian', 'Ubuntu'] %}
ntpdate-svc:
  service.enabled:
    - name: ntpdate
{%- endif %}

ntpd:
  service.running:
    - enable: True
    {%- if grains['os'] in ['Debian', 'Ubuntu'] %}
    - name: ntp
    {%- endif %}
    - watch:
      - file: {{ locs.conf_dir }}/ntp.conf
      - pkg: ntp-pkgs

{{ locs.conf_dir }}/ntp.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://makina-states/files/etc/ntp.conf
    - var_lib: {{ locs.var_lib_dir }}
    - require:
      - pkg: ntp-pkgs

{{ locs.conf_dir }}/default/ntpdate:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://makina-states/files/etc/default/ntpdate
    - require:
      - pkg: ntp-pkgs

