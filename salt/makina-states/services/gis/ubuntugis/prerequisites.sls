include:
  - makina-states.services.gis.ubuntugis.hooks
  - makina-states.services.db.postgresql.hooks
{% set settings = salt['mc_ubuntugis.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set ppa = settings.ubuntu_ppa %}
{% set dist = settings.dist %}

{% if grains['os_family'] in ['Debian'] %}
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
{% if grains.get('osrelease') > '14.04' %}
  file.absent:
    - names:
      - {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/pgrouting.list
    - watch_in:
      - pkg: ubuntugis-pkgs
{% else %}
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
{% endif %}
{% endif %}

ubuntugis-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
    {% for i in settings.pkgs %}
      - "{{i}}"
    {% endfor %}
    - watch:
      - mc_proxy: ubuntugis-pre-install-hook
    - watch_in:
      - mc_proxy: ubuntugis-pre-hardrestart-hook
      - mc_proxy: ubuntugis-post-install-hook
