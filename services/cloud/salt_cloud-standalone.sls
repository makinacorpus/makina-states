{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set localsettings = services.localsettings %}

{% macro do(full=False) %}
{{- salt['mc_macros.register']('services', 'cloud.salt_cloud') }}
{% if full %}
include:
  makina-states.services.controllers
{% endif %}

{% if controllers.registry.is.mastersalt_master %}
{% set prefix = saltmac.mconfPrefix %}
{% else %}
{% set prefix = saltmac.confPrefix %}
{% endif %}


{% set pvdir = prefix+'/cloud.providers.d' %}
{% set pfdir = prefix+'/cloud.profiles.d' %}
salt_cloud-dirs:
  file.directory:
    - names:
      - {{pvdir}}
      - {{pfdir}}
    - makedirs: true
    - user: root
    - group: {{localsettings.group }}
    - mode: 2770

lxc_salt_ssh:
  file.managed:
    - source: ''
    - name: {{pvdir}}/makinastates_minion.conf
    - user: root
    - group: root
    - require:
      - file: salt_cloud-dirs
    - contents: |
                providers:
                  - id: lxc-{{opts['id']}}:
                    minion: {{opts['id']}}
                    provider: lxc

{% endmacro %}
{{do(full=False)}}
