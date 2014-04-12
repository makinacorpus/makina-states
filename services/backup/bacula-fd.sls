{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.bacula-fd') }}

bacula-fd-pkg:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
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
