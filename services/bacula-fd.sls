bacula-fd:
  pkg:
    - installed
  service:
    - enabled

/etc/bacula/bacula-fd.conf:
  bacula.fdconfig:
    - require:
      - pkg: bacula-fd
    - dirname: makina-dir
    - dirpasswd: {{ pillar.get('bacula-dir-pw', 'baculapw') }}
    - fdname: {{ grains['id'] }}
    - fdport: 9102
    - messages: bacula-dir = all, !skipped, !restored

