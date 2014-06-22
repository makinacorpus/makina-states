include:
  - makina-states.services.gis.ubuntugis.hooks
  - makina-states.services.db.postgresql.hooks

{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_ubuntugis.settings']() %}
{% if grains['os_family'] in ['Debian'] %}
{% set dist = pkgssettings.udist %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% set dist = pkgssettings.ubuntu_lts %}
{% endif %}
{% if settings.ppa == 'unstable' %}
{%  set ppa = 'ubuntugis-unstable' %}
{% elif settings.ppa == 'testing' %}
{%  set ppa = 'ubuntugis-testing' %}
{% else %}
{%  set ppa ='ppa'%}
{% endif %}
{% if dist in ['trusty'] %}
{%  set ppa = 'ubuntugis-unstable' %}
{% endif %}

ubuntugis-base:
  pkgrepo.managed:
    - humanname: ubuntugis ppa
    - name: deb http://ppa.launchpad.net/ubuntugis/{{ppa}}/ubuntu {{dist}} main
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/ubuntugis.list
    - keyid: 314DF160
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: makina-postgresql-post-pkg
    - watch_in:
      - pkg: ubuntugis-pkgs

ubuntugis-pgrouting-base:
  pkgrepo.managed:
    - humanname: ubuntugis pgrouting ppa
    - name: deb http://ppa.launchpad.net/georepublic/pgrouting/ubuntu {{dist}} main
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/pgrouting.list
    - keyid: B65ADE33
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: makina-postgresql-post-pkg
    - watch_in:
      - pkg: ubuntugis-pkgs

ubuntugis-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - libgeos-dev
    - watch:
      - mc_proxy: ubuntugis-pre-install-hook
    - watch_in:
      - mc_proxy: ubuntugis-pre-hardrestart-hook
      - mc_proxy: ubuntugis-post-install-hook
