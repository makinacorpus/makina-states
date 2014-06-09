{#-
# Install several python versions (ubuntu specific for now),see standalone
#  see:
#   -  makina-states/doc/ref/formulaes/localsettings/python.rst
#}
{{ salt['mc_macros.register']('localsettings', 'python') }}
include:
  - makina-states.localsettings.pkgs.mgr
{% endif %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set pyvers = salt['mc_python.settings']().alt_versions %}
{%- if (grains['os'] in ['Ubuntu']) and pyvers %}
{%- set udist = salt['mc_pkgs.settings']().udist %}
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
      - file: apt-sources-list
      - cmd: apt-update-after
    - pkgs:
      {%- for pyver in pyvers %}
      - python{{pyver}}-dev
      - python{{pyver}}
      - python-pip
      {%- endfor %}
    {%- endif %}
# vim:set nofoldenable:
