{#-
# Install several python versions (ubuntu specific for now),see standalone
#  see:
#   -  makina-states/doc/ref/formulaes/localsettings/python.rst
#}
{% macro do(full=True) %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'python') }}
{% if full %}
include:
  - makina-states.localsettings.pkgmgr
{% endif %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set pyvers = localsettings.pythonSettings.alt_versions %}
{%- if (grains['os'] in ['Ubuntu']) and pyvers %}
{%- set udist = localsettings.udist %}
deadsnakes:
  pkgrepo.managed:
    - humanname: DeadSnakes PPA
    - name: deb http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu {{udist}} main
    - dist: {{udist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/deadsnakes.list
    - keyid: DB82666C
    - keyserver: keyserver.ubuntu.com
  {%- if pyvers %}
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require:
      - pkgrepo: deadsnakes
      {% if full %}
      - file: apt-sources-list
      - cmd: apt-update-after
      {% endif %}
    - pkgs:
      {%- for pyver in pyvers %}
      - python{{pyver}}-dev
      - python{{pyver}}
      - python-pip
      {%- endfor %}
    {%- endif %}
{% endif %}
{# be sure to have at least one state #}
python-last-hook:
  mc_proxy.hook:
    - order: last
{% endmacro %}
{{ do(full=False) }}
# vim:set nofoldenable:
