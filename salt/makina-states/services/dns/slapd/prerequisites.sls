{% set settings = salt['mc_slapd.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.dns.slapd.hooks
slapd_removedebpkg:
  file.absent:
    - names:
        - "{{settings.slapd_directory}}/cn=config/olcBackend={0}mdb.ldif"
        - "{{settings.slapd_directory}}/cn=config/olcDatabase={1}mdb.ldif"
    - watch:
      - mc_proxy: slapd-pre-install
    - watch_in:
      - mc_proxy: slapd-post-install
      - pkg: slapd-pkgs

slapd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: slapd-pre-install
    - watch_in:
      - mc_proxy: slapd-post-install

slapd-dirs:
  file.directory:
    - names:
      {% for d in settings.extra_dirs %}
      - "{{d}}"
      {% endfor %}
    - makedirs: true
    - user: root
    - group: {{settings.group}}
    - mode: 775
    - watch:
      - mc_proxy: slapd-post-install
    - watch_in:
      - mc_proxy: slapd-pre-conf

