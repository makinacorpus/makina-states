{#-
# Install several python versions (ubuntu specific for now),see standalone
#  see:
#   -  makina-states/doc/ref/formulaes/localsettings/python.rst
#}
{{ salt['mc_macros.register']('localsettings', 'python') }}
include:
  - makina-states.localsettings.pkgs.mgr
{%- set locs = salt['mc_locations.settings']() %}
{%- set udist = salt['mc_pkgs.settings']().udist %}
{%- set pyvers = salt['mc_python.settings']().alt_versions %}
{%- if (grains['os'] in ['Ubuntu'])%}
deadsnakes-ppa:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: DeadSnakes PPA
    - name: deb http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu {{udist}} main
    - dist: {{udist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/deadsnakes.list
    - keyid: DB82666C
    - keyserver: keyserver.ubuntu.com
{%- if  pyvers %}
deadsnakes:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require:
      - pkgrepo: deadsnakes-ppa
      - file: apt-sources-list
      - cmd: apt-update-after
    - pkgs:
      {%- for pyver in pyvers %}
      - python{{pyver}}-dev
      - python{{pyver}}
      - python-pip
      {%- endfor %}
{%- endif %}
{%- endif %}
# vim:set nofoldenable:
