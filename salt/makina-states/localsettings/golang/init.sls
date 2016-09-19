{#-
# Install several golang versions (ubuntu specific for now),see standalone
#}
{{ salt['mc_macros.register']('localsettings', 'golang') }}
include:
  - makina-states.localsettings.pkgs.mgr
{%- set data = salt['mc_golang.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- if (grains['os'] in ['Ubuntu'])%}
golang-ppa:
  pkgrepo.managed:
    - name: deb {{data.ppa}} {{data.dist}} main
    - dist: {{data.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/golang.list
    - keyid: 9AD198E9
    - keyserver: keyserver.ubuntu.com
{%- if data.packages %}
golang-pkg:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require:
      - pkgrepo: golang-ppa
    - pkgs: {{data.packages}}
{%- endif %}
{%- endif %}

golang-bins:
  cmd.run:
    - require:
      - pkg: golang-pkg
    - name: |
            set -e
            {%- for j in data.bins %}
            update-alternatives --quiet --remove-all {{j}} || true;
            {%- for i in data.versions %}
            update-alternatives --quiet --install /usr/local/bin/{{j}} {{j}} /usr/lib/go-{{i}}/bin/{{j}} 0;
            {% endfor%}
            update-alternatives --quiet --set {{j}} /usr/lib/go-{{data.version}}/bin/{{j}};
            {% endfor %}
# vim:set nofoldenable:
