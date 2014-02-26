{% macro do(full=True) %}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'base.ntp') }}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}

include:
  - makina-states.localsettings.timezone

{% if full %}
ntp-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - ntp
      - ntpdate
{% endif %}

{%- if grains['os'] not in ['Debian', 'Ubuntu'] %}
ntpdate-svc:
  service.enabled:
    - name: ntpdate
    {% if full %}
    - require:
      - pkg: ntp-pkgs
    {% endif %}
{%- endif %}

ntpd:
  service.running:
    - enable: True
    {%- if grains['os'] in ['Debian', 'Ubuntu'] %}
    - name: ntp
    {%- endif %}
    - watch:
      - file: {{ locs.conf_dir }}/ntp.conf
    {% if full %}
      - pkg: ntp-pkgs
    {% endif %}

{{ locs.conf_dir }}/ntp.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://makina-states/files/etc/ntp.conf
    - var_lib: {{ locs.var_lib_dir }}
    {% if full %}
    - require:
      - pkg: ntp-pkgs
    {% endif %}

{{ locs.conf_dir }}/default/ntpdate:
  file.managed:
    - user: root
    - group: root
    - mode: '0440'
    - template: jinja
    - source: salt://makina-states/files/etc/default/ntpdate
    {% if full %}
    - require:
      - pkg: ntp-pkgs
    {% endif %}

{% endmacro %}
{{ do(full=False) }}
