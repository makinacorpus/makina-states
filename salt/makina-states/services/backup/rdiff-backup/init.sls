{#- Integration of rdiff-backup, a file backup software #}
{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.rdiff-backup') }}
{%- set data=salt['mc_rdiffbackup.settings']() %}
{%- set settings = salt['mc_utils.json_dump'](salt['mc_rdiffbackup.settings']()) %}
remove-rdiff-backup-pkgs:
  pkg.removed:
    - pkgs:
      - rdiff-backup
rdiff-backup-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require:
      - pkg: remove-rdiff-backup-pkgs
    - pkgs:
      - rdiff-backup
      - rdiff-backup-fs
      - librsync-dev
      - librsync1
      - python-dev
      - libattr1
      - libattr1-dev
      - libacl1
      - libacl1-dev
