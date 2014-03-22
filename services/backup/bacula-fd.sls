{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set locs = salt['mc_localsettings']()['locations'] %}
{{ salt['mc_macros.register']('services', 'backup.bacula-fd') }}

bacula-fd-pkg:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - bacula-fd

bacula-fd-svc:
  service.nablede:
    - name:  bacula-fd
    - require:
      - file: etc-bacula-bacula-fd.conf

etc-bacula-bacula-fd.conf:
  bacula.fdconfig:
    - name: {{ locs.conf_dir }}/bacula/bacula-fd.conf
    - require:
      - pkg: bacula-fd-pkgs
    - dirname: makina-dir
    - dirpasswd: {{ pillar.get('bacula-dir-pw', 'baculapw') }}
    - fdname: {{ grains['id'] }}
    - fdport: 9102
    - messages: bacula-dir = all, !skipped, !restored
